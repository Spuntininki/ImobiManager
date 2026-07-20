"""Shared Telegram message types (kept here to avoid router/poller cycles)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InboundMessage:
    """Normalized inbound Telegram message."""

    update_id: int
    chat_id: int
    text: str
