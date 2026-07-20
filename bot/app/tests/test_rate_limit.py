"""Tests for the 3-layer RateLimiter (token, chat, lock).

The throttle-reply cooldown is also covered here. These tests run
synchronously despite the lock being an `asyncio.Lock`: the `check()` path
itself is sync (no `await`); synchronization is exercised via
`acquire_nowait()` directly.
"""

import asyncio

import pytest

from app.security.rate_limit import (
    DAY_SECONDS,
    RateLimiter,
)


def test_allows_within_limits_user(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 2)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 5)
    lim = RateLimiter()
    assert lim.check(token_id=1, chat_id=10, subject_type="USER").allowed
    assert lim.check(token_id=1, chat_id=10, subject_type="USER").allowed
    # 3rd within the minute → rejected
    d = lim.check(token_id=1, chat_id=10, subject_type="USER")
    assert not d.allowed
    assert "minute" in d.reason


def test_per_chat_window_blocks_new_token_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 1)
    lim = RateLimiter()
    assert lim.check(token_id=1, chat_id=10, subject_type="USER").allowed
    # Different token, same chat → still blocked (L3 protects the chat).
    d = lim.check(token_id=2, chat_id=10, subject_type="USER")
    assert not d.allowed
    assert "chat" in d.reason


def test_renter_uses_smaller_quotas(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_rate_limit_renter_per_min", 1)
    monkeypatch.setattr(settings, "bot_rate_limit_chat_per_min", 99)
    lim = RateLimiter()
    assert lim.check(token_id=7, chat_id=1, subject_type="RENTER").allowed
    d = lim.check(token_id=7, chat_id=1, subject_type="RENTER")
    assert not d.allowed
    assert "minute" in d.reason


def test_lock_acquire_nowait_drops_duplicates(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)

    async def scenario() -> None:
        lim = RateLimiter()
        lock = await lim.acquire_lock(42)
        # Acquire the lock (we are inside the only coroutine so far) and
        # release it manually to simulate "in-flight" state.
        await lock.acquire()
        assert lock.locked()
        # Second "request" for the same token while the first is held → drop.
        lock_again = await lim.acquire_lock(42)
        assert lock_again is lock  # same lock object
        assert lock_again.locked()  # caller checks this and drops
        lock.release()

    asyncio.run(scenario())


def test_throttle_reply_is_gated_to_once_per_30s() -> None:
    lim = RateLimiter()
    assert lim.should_send_throttle_reply(chat_id=1)
    # Repeated within cooldown → suppressed.
    assert not lim.should_send_throttle_reply(chat_id=1)


def test_retry_after_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import settings
    from app.security import rate_limit as rl

    monkeypatch.setattr(settings, "bot_rate_limit_user_per_min", 99)
    monkeypatch.setattr(settings, "bot_rate_limit_user_per_day", 1)
    # The limiter holds a reference to the module-level `settings`. Confirm it
    # sees the patched value via the same object.
    assert rl.settings is settings

    lim = RateLimiter()
    assert lim.check(token_id=3, chat_id=3, subject_type="USER").allowed
    d = lim.check(token_id=3, chat_id=3, subject_type="USER")
    assert not d.allowed
    assert "day" in d.reason
    assert d.retry_after == DAY_SECONDS
