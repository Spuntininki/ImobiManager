"""Hard-reject rate limiter (3 layers, in-memory, no Redis).

Layers (all evaluated on every inbound message with a valid token):

- L2 token_id  : per-token rolling minute + sliding day counter;
                 limits differ by subject_type (USER vs RENTER).
- L3 chat_id   : protects against a single Telegram chat firing via multiple
                 tokens; one rolling minute window.
- lock         : exactly one message processed at a time per token; any
                 duplicate during processing is silently discarded.

A backpressure layer (max concurrent LLMs) is intentionally out of scope for
the MVP — see the plan. Scaling the bot to multiple replicas also breaks
these in-memory windows; that is a documented limitation (the windows are
per-pod and do not share state).

The throttling output message ("você atingiu o limite…") is sent at most
once per 30s per chat_id, so a flood of rejects does not produce a flood of
replies.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60
DAY_SECONDS = 86_400
THROTTLE_REPLY_COOLDOWN = 30.0


@dataclass(frozen=True, slots=True)
class Decision:
    """Result of `check()`."""

    allowed: bool
    reason: str
    retry_after: float
    """Seconds the caller should wait before sending again (0 when allowed)."""


class _Window:
    """Rolling-window counter of timestamps within `ttl` seconds."""

    __slots__ = ("ttl", "events")

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.events: deque[float] = deque()

    def _trim(self, now: float) -> None:
        cutoff = now - self.ttl
        while self.events and self.events[0] < cutoff:
            self.events.popleft()

    def count(self) -> int:
        now = time.monotonic()
        self._trim(now)
        return len(self.events)

    def record(self) -> None:
        self.events.append(time.monotonic())


class _Entry:
    """Per-token bookkeeping for L2 minute + day windows."""

    __slots__ = ("minute", "day")

    def __init__(self) -> None:
        self.minute = _Window(WINDOW_SECONDS)
        self.day = _Window(DAY_SECONDS)


class RateLimiter:
    """3-layer hard-reject state for the whole bot pod."""

    def __init__(self) -> None:
        self._tokens: dict[int, _Entry] = {}
        self._per_minute_by_chat: dict[int, _Window] = _windows_factory()
        self._locks: dict[int, asyncio.Lock] = {}
        self._last_throttle_reply: dict[int, float] = {}

    # --- public API -------------------------------------------------------

    async def acquire_lock(self, token_id: int) -> asyncio.Lock:
        """Return the lock for `token_id`, creating it lazily.

        The caller should test `if lock.locked(): drop` BEFORE awaiting
        `async with lock:`, so that an already-in-flight message for this
        token is discarded instead of queued. asyncio.Lock has no
        `acquire_nowait`, but the `locked()` + awaiting `acquire()` pattern
        is close enough for the single-pod single-loop MVP — a real
        backpressure primitive (semaphore + queue) is deferred (see plan).
        """
        lock = self._locks.get(token_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[token_id] = lock
        return lock

    def check(self, *, token_id: int, chat_id: int, subject_type: str) -> Decision:
        """Decide whether the message may proceed (L2 + L3).

        Must be called WITH the per-token lock held so the counters do not
        race. On `allowed=True` the caller is expected to actually proceed
        with the LLM call, since the act of calling consumes the quota.
        """
        now = time.monotonic()

        per_min, per_day = self._limits_for(subject_type)
        entry = self._ensure_token_entry(token_id)
        entry.minute._trim(now)  # noqa: SLF001 — internal window access
        entry.day._trim(now)  # noqa: SLF001

        if entry.minute.count() >= per_min:
            return Decision(False, "rate_limit_per_minute", WINDOW_SECONDS)
        if entry.day.count() >= per_day:
            return Decision(False, "rate_limit_per_day", DAY_SECONDS)

        chat_window = self._per_minute_by_chat.get(chat_id)
        if chat_window is not None and chat_window.count() >= settings.bot_rate_limit_chat_per_min:
            return Decision(False, "rate_limit_per_chat", WINDOW_SECONDS)

        # Consume the quota now (inside the lock).
        entry.minute.record()
        entry.day.record()
        if chat_window is None:
            chat_window = _Window(WINDOW_SECONDS)
            self._per_minute_by_chat[chat_id] = chat_window
        chat_window.record()
        return Decision(True, "ok", 0.0)

    def should_send_throttle_reply(self, chat_id: int) -> bool:
        """Gate throttle replies to at most one per 30s per chat."""
        now = time.monotonic()
        last = self._last_throttle_reply.get(chat_id, 0.0)
        if now - last >= THROTTLE_REPLY_COOLDOWN:
            self._last_throttle_reply[chat_id] = now
            return True
        return False

    # --- internals --------------------------------------------------------

    def _limits_for(self, subject_type: str) -> tuple[int, int]:
        if subject_type == "RENTER":
            return (
                settings.bot_rate_limit_renter_per_min,
                settings.bot_rate_limit_renter_per_day,
            )
        # USER is the default; unknown subject types get the user limits.
        return (
            settings.bot_rate_limit_user_per_min,
            settings.bot_rate_limit_user_per_day,
        )

    def _ensure_token_entry(self, token_id: int) -> _Entry:
        entry = self._tokens.get(token_id)
        if entry is None:
            entry = _Entry()
            self._tokens[token_id] = entry
        return entry


def _windows_factory() -> dict[int, _Window]:
    """Factory kept explicit so type checkers infer `dict[int, _Window]`."""
    return {}
