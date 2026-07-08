"""Pydantic schemas for the revenue timeline dashboard feature."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RevenueTimelineItem(BaseModel):
    """A single projected revenue payment for the dashboard timeline chart."""

    model_config = ConfigDict(from_attributes=True)

    payment_date: date = Field(..., description="Payment date (owner-local calendar day).")
    amount: Decimal = Field(..., description="Projected payment amount.")


class RevenueTimelineSummary(BaseModel):
    """Aggregated summary for the requested date range."""

    total_amount: Decimal = Field(..., description="Sum of all projected payments.")
    total_payments: int = Field(..., description="Number of projected payments.")
