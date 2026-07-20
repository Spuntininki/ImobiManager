"""Message router: turns a Telegram text message into a bot reply.

The router is the single point that combines all bot concerns for one inbound
message:

1. Parse the message (token vs. plain onboarding text).
2. If no token → answer with a generic help message (no LLM cost).
3. If token → validate against the backend (with cache).
4. Acquire the per-token lock (one in-flight per client).
5. Check rate limits (L2 + L3). On reject → send a throttle reply at most
   once per 30s per chat.
6. Open an MCP `ClientSession`, run the agent, send the reply.
7. Always record IN/OUT logs (best-effort).

Authentication note: token validation failures (unknown, revoked, expired,
wrong chat) all map to "no auth" — we do NOT tell the user which case
applied, to avoid token reconnaissance. We still send the onboarding hint
because the subject_type is unknown, so we cannot run the LLM anyway.
"""

from __future__ import annotations

import logging

from app.logging.message_log_publisher import MessageLogPublisher
from app.platforms.telegram.client import TelegramClient
from app.platforms.telegram.types import InboundMessage
from app.security.rate_limit import RateLimiter
from app.security.token_auth import ParsedCommand, TokenAuthenticator, parse_message

logger = logging.getLogger(__name__)

ONBOARDING_TEXT = (
    "Olá! Eu sou o assistente do ImobiManager. 🏠\n\n"
    "Para conversar comigo, você precisa de um token de acesso gerado pelo "
    "proprietário/administrador no site. Envie:\n\n"
    "  /start SEU_TOKEN\n\n"
    'Depois disso é só fazer suas perguntas normalmente (ex.: "quantos '
    'imóveis eu tenho?", "qual o vencimento do meu aluguel?").'
)

RATE_LIMIT_TEXT = (
    "Você atingiu o limite de mensagens. Aguarde alguns instantes e tente novamente, por favor. 🕒"
)

LINKED_TEXT = "Token validado! A partir de agora você pode conversar normalmente. 👍"


class MessageRouter:
    """Glue for one inbound message end-to-end."""

    def __init__(
        self,
        *,
        auth: TokenAuthenticator,
        limiter: RateLimiter,
        agent_runner,
        log_publisher: MessageLogPublisher,
    ) -> None:
        self._auth = auth
        self._limiter = limiter
        self._agent = agent_runner
        self._logs = log_publisher

    async def route(self, msg: InboundMessage, tg: TelegramClient) -> None:
        parsed = parse_message(msg.text)
        self._logs.record(token_id=None, chat_id=msg.chat_id, direction="IN", llm_tokens_used=0)

        if parsed.token is None:
            await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return

        result = await self._auth.validate(parsed.token, msg.chat_id)
        if result is None:
            await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return

        lock = await self._limiter.acquire_lock(result.token_id)
        if lock.locked():
            # Already processing one message for this token → drop silently.
            logger.debug("dropping duplicate message for token_id=%s", result.token_id)
            return
        async with lock:
            decision = self._limiter.check(
                token_id=result.token_id,
                chat_id=msg.chat_id,
                subject_type=result.subject_type,
            )
            if not decision.allowed:
                if self._limiter.should_send_throttle_reply(msg.chat_id):
                    await tg.send_message(msg.chat_id, RATE_LIMIT_TEXT)
                    self._logs.record(
                        token_id=result.token_id,
                        chat_id=msg.chat_id,
                        direction="OUT",
                        llm_tokens_used=0,
                    )
                return

            body = parsed.body or "Olá"
            reply = await self._run_agent(
                subject_type=result.subject_type,
                subject_id=result.subject_id,
                chat_id=msg.chat_id,
                body=body,
            )
            await tg.send_message(msg.chat_id, reply)
            self._logs.record(
                token_id=result.token_id,
                chat_id=msg.chat_id,
                direction="OUT",
                llm_tokens_used=0,
            )

    async def _run_agent(
        self,
        *,
        subject_type: str,
        subject_id: int,
        chat_id: int,
        body: str,
    ) -> str:
        """Invoke the agent runner with our standard 4-keyword signature.

        Kept as a thin wrapper so test doubles can replace it without
        touching the real LangChain agent, and so failures are translated
        into a user-facing apology rather than propagating upstream.
        """
        try:
            return await self._agent.run(
                chat_id=chat_id,
                user_text=body,
                subject_type=subject_type,
                subject_id=subject_id,
            )
        except Exception as exc:
            logger.exception(
                "agent run failed chat_id=%s subject_id=%s: %s",
                chat_id,
                subject_id,
                exc,
            )
            return (
                "Tive um problema ao processar sua mensagem agora. "
                "Tente novamente em alguns instantes."
            )


__all__ = ["MessageRouter", "parse_message", "ParsedCommand"]
