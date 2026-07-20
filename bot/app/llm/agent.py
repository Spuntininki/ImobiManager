"""LangChain agent wiring (ChatOpenAI → OpenRouter + tools + per-chat history).

The agent is built ONCE at pod startup:

- `ChatOpenAI` pointed at the OpenRouter `base_url` with the choosen `model`.
- Tools from `app.llm.tools` (MCP-backed, read-only).
- System prompt assembled from `prompts/system.md` + `roles/<subject>.md` +
  `prompts/guardrails.md`.

Per-message flow (handled by `AgentRunner.run`):

1. The router opened an MCP `ClientSession` against `/mcp`.
2. `set_session(session)` pins it into a ContextVar the tools read from.
3. The chat-history store replays the last N messages for the chat.
4. `agent.ainvoke({"messages": [...]})` runs the tool-calling loop.
5. The final AIMessage text is returned; we truncate before sending back.

History is in-memory per chat_id (truncated to a small window). A multi-pod
deployment would need a shared store — documented as debt.

LangChain usage notes: version 1.x ships `langchain.agents.create_agent`,
which returns a compiled LangGraph agent. Input is `{"messages": [...]}` and
the output dict has a `messages` key holding the final message list.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.llm.mcp_client import connect
from app.llm.tools import ALL_TOOLS, reset_session, set_session

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_HISTORY_MAX = 12  # pairs of turns kept per chat
_MAX_REPLY_CHARS = 1500


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_system_prompt(subject_type: str) -> str:
    """Compose the system prompt for the given role."""
    role_file = "roles/user.md" if subject_type == "USER" else "roles/renter.md"
    return (
        _load("system.md").replace("{subject_type}", subject_type)
        + "\n\n"
        + _load(role_file)
        + "\n\n"
        + _load("guardrails.md")
    )


class ChatHistory:
    """In-memory bounded chat history per chat_id."""

    def __init__(self) -> None:
        self._store: dict[int, deque[BaseMessage]] = defaultdict(lambda: deque(maxlen=_HISTORY_MAX))

    def extend(self, chat_id: int, messages: list[BaseMessage]) -> None:
        self._store[chat_id].extend(messages)

    def recent(self, chat_id: int) -> list[BaseMessage]:
        return list(self._store[chat_id])


class AgentRunner:
    """Glue between the router and the LangChain agent."""

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=0.2,
            max_tokens=800,
        )
        # The agent is role-agnostic: we rebuild the system prompt per message
        # (cheap) and pass it as the first message in the input. Building the
        # agent once with no system_prompt keeps the compiled graph reusable.
        self._agent = create_agent(model=self._llm, tools=ALL_TOOLS)
        self._history = ChatHistory()


async def run(
    self,
    *,
    chat_id: int,
    user_text: str,
    subject_type: str,
    subject_id: int,
) -> str:
    """Open a fresh MCP session, run one turn of the agent, return reply.

    The session lifetime is bounded to this single run; per-run closing
    in the connected `connect()` async context manager. The agent itself
    is reused (compiled once at startup).
    """
    async with connect(subject_type=subject_type, subject_id=subject_id) as session:
        token = set_session(session)
        try:
            messages: list[BaseMessage] = [
                SystemMessage(content=build_system_prompt(subject_type)),
                *self._history.recent(chat_id),
                HumanMessage(content=user_text),
            ]
            result = await self._agent.ainvoke({"messages": messages})
        finally:
            reset_session(token)

    output_messages = result.get("messages", []) if isinstance(result, dict) else []
    final = next(
        (m for m in reversed(output_messages) if isinstance(m, AIMessage)),
        None,
    )
    reply = (final.content if isinstance(final, AIMessage) else "").strip()
    if not reply:
        reply = "Não consegui gerar uma resposta agora. Tente reformular sua pergunta."
    if len(reply) > _MAX_REPLY_CHARS:
        reply = reply[:_MAX_REPLY_CHARS] + "…"
    # Persist this turn into history for the next invocation.
    self._history.extend(chat_id, [HumanMessage(content=user_text), AIMessage(content=reply)])
    return reply
