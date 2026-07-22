"""Message router: turns a Telegram text message into a bot reply.

The router is the single point that combines all bot concerns for one inbound
message:

1. Log the inbound message (best-effort).
2. Dispatch commands (`/start`, `/help`, `/logout`).
3. If no command, look up the chat session (token cached from a prior
   `/start`). If found, validate (cached, fast) and run the agent using the
   full message text as the body.
4. If no session, try to parse a `<TOKEN> <body>` prefix from the message;
   on success, validate + bind + run the agent.
5. If neither, answer with the generic onboarding hint (no LLM cost).
6. Always record IN/OUT logs (best-effort).

Token validation failures (unknown, revoked, expired, wrong chat) all map to
"no auth" — the bot sends the onboarding hint without distinguishing cases,
to avoid token reconnaissance. When a previously-linked session fails to
validate, the session is cleared so the chat falls back to onboarding.
"""

from __future__ import annotations

import logging

from app.logging.message_log_publisher import MessageLogPublisher
from app.platforms.telegram.client import TelegramClient
from app.platforms.telegram.types import InboundMessage
from app.security.rate_limit import RateLimiter
from app.security.token_auth import (
    ChatSessionStore,
    ParsedCommand,
    TokenAuthenticator,
    parse_message,
)

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

ALREADY_LINKED_TEXT = (
    "Você já está conectado. Para trocar de token, envie /start NOVO_TOKEN. "
    "Para sair, envie /logout."
)

LOGOUT_TEXT = "Desconectado. Para conectar novamente, envie /start SEU_TOKEN."

HELP_TEXT = (
    "Comandos disponíveis:\n\n"
    "  /start TOKEN — conectar (ou trocar de token)\n"
    "  /logout — desconectar\n"
    "  /help — mostrar esta ajuda\n\n"
    'Após /start, é só enviar suas perguntas normalmente (ex.: "quantos '
    'imóveis eu tenho?").'
)

_START_CMD = "/start"
_HELP_CMD = "/help"
_LOGOUT_CMD = "/logout"
_COMMANDS = (_START_CMD, _HELP_CMD, _LOGOUT_CMD)


class MessageRouter:
    """Glue for one inbound message end-to-end."""

    def __init__(
        self,
        *,
        auth: TokenAuthenticator,
        limiter: RateLimiter,
        agent_runner: object,
        log_publisher: MessageLogPublisher,
        sessions: ChatSessionStore,
    ) -> None:
        self._auth = auth
        self._limiter = limiter
        self._agent = agent_runner
        self._logs = log_publisher
        self._sessions = sessions

    # ------------------------------------------------------------------ #
    # Public entry point                                                 #
    # ------------------------------------------------------------------ #

    async def route(self, msg: InboundMessage, tg: TelegramClient) -> None:
        self._logs.record(token_id=None, chat_id=msg.chat_id, direction="IN", llm_tokens_used=0)
        text = msg.text.strip()

        # --- Commands ----------------------------------------------------
        if text.startswith(_START_CMD):
            await self._handle_start(msg, tg, text)
            return
        if text == _HELP_CMD or text.startswith(_HELP_CMD):
            await tg.send_message(msg.chat_id, HELP_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return
        if text == _LOGOUT_CMD or text.startswith(_LOGOUT_CMD):
            self._sessions.clear(msg.chat_id)
            await tg.send_message(msg.chat_id, LOGOUT_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return

        # --- Session lookup (no command, maybe already linked) ----------
        session_token = self._sessions.get(msg.chat_id)
        if session_token is not None:
            await self._run_with_session_token(msg, tg, session_token, text)
            return

        # --- No session: try <TOKEN> <body> ------------------------------
        parsed = parse_message(text)
        if parsed.token is None:
            await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return
        await self._run_with_parsed_token(msg, tg, parsed.token, parsed.body or text)

    # ------------------------------------------------------------------ #
    # Command handlers                                                   #
    # ------------------------------------------------------------------ #

    async def _handle_start(self, msg: InboundMessage, tg: TelegramClient, text: str) -> None:
        """Handle `/start [TOKEN] [optional question]`."""
        parts = text.split(maxsplit=2)  # ["/start", "TOKEN", "rest..."]
        if len(parts) < 2:
            # `/start` with no token.
            if self._sessions.get(msg.chat_id) is not None:
                await tg.send_message(msg.chat_id, ALREADY_LINKED_TEXT)
            else:
                await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return

        token = parts[1].strip()
        body = parts[2].strip() if len(parts) >= 3 else ""
        await self._run_with_parsed_token(msg, tg, token, body)

    # ------------------------------------------------------------------ #
    # Agent execution (shared by all paths)                             #
    # ------------------------------------------------------------------ #

    async def _run_with_session_token(
        self, msg: InboundMessage, tg: TelegramClient, token: str, body: str
    ) -> None:
        """Validate a cached session token and run the agent with the full text."""
        result = await self._auth.validate(token, msg.chat_id)
        if result is None:
            # Session token expired/revoked — clear and fall back to onboarding.
            self._sessions.clear(msg.chat_id)
            await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return
        await self._run_agent(msg, tg, result, body)

    async def _run_with_parsed_token(
        self, msg: InboundMessage, tg: TelegramClient, token: str, body: str
    ) -> None:
        """Validate a token from `/start` or `<TOKEN> …`, bind on first success, run agent."""
        result = await self._auth.validate(token, msg.chat_id)
        if result is None:
            await tg.send_message(msg.chat_id, ONBOARDING_TEXT)
            self._logs.record(
                token_id=None, chat_id=msg.chat_id, direction="OUT", llm_tokens_used=0
            )
            return
        # Bind this chat to the token for future messages.
        self._sessions.set(msg.chat_id, token)
        # If no body (e.g. `/start TOKEN`), just confirm the link.
        if not body:
            await tg.send_message(msg.chat_id, LINKED_TEXT)
            self._logs.record(
                token_id=result.token_id,
                chat_id=msg.chat_id,
                direction="OUT",
                llm_tokens_used=0,
            )
            return
        await self._run_agent(msg, tg, result, body)

    async def _run_agent(self, msg: InboundMessage, tg: TelegramClient, result, body: str) -> None:
        """Check rate limits and invoke the agent."""
        lock = await self._limiter.acquire_lock(result.token_id)
        if lock.locked():
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

            reply = await self._invoke_agent(
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

    async def _invoke_agent(
        self,
        *,
        subject_type: str,
        subject_id: int,
        chat_id: int,
        body: str,
    ) -> str:
        """Invoke the agent runner, translating unhandled exceptions to a friendly reply."""
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
