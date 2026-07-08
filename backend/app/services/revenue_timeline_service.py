"""Business logic for the owner revenue timeline dashboard feature."""

import calendar
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contract
from app.models.enums import ContractStatus


def _add_months(value: date, months: int) -> date:
    """Return a date shifted by the given number of months, clamping the day
    to the last valid day of the target month.
    """
    year = value.year + (value.month + months - 1) // 12
    month = (value.month + months - 1) % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(value.day, last_day))


def _generate_contract_payment_dates(
    start_date: date,
    end_date: date,
    payment_day: int,
) -> list[date]:
    """Generate the monthly payment dates for a single contract.

    The first payment is the first occurrence of `payment_day` on or after
    `start_date`. Subsequent payments are monthly until `end_date` (inclusive).
    Days beyond the target month's length are clamped to its last day.
    """
    if start_date > end_date:
        return []

    first_candidate = date(start_date.year, start_date.month, payment_day)
    if first_candidate < start_date:
        first_candidate = _add_months(first_candidate, 1)

    dates: list[date] = []
    current = first_candidate
    while current <= end_date:
        dates.append(current)
        current = _add_months(current, 1)

    return dates


def _default_date_range() -> tuple[date, date]:
    """Return the default 12-month dashboard window starting from today."""
    today = date.today()
    # Approximate 12 months by subtracting one day from the same day next year.
    end = (today.replace(year=today.year + 1)) - timedelta(days=1)
    return today, end


async def generate_owner_revenue_timeline(
    session: AsyncSession,
    owner_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[list[dict], Decimal, int]:
    """Generate an aggregated revenue timeline for an owner.

    Only ACTIVE contracts are considered. CANCELLED and EXPIRED contracts are
    excluded by design (the front-end dashboard projects future/already-active
    revenue only).

    Returns a tuple of (timeline_items, total_amount, total_payments).
    """
    range_start, range_end = (
        (start_date, end_date)
        if start_date is not None and end_date is not None
        else _default_date_range()
    )

    result = await session.execute(
        select(Contract).where(
            Contract.owner_id == owner_id,
            Contract.status == ContractStatus.ACTIVE,
        )
    )
    contracts = result.scalars().all()

    totals_by_date: dict[date, Decimal] = defaultdict(Decimal)

    for contract in contracts:
        contract_start = contract.start_date.date()
        contract_end = contract.end_date.date()

        # The contract window is [start_date, end_date]; the requested range
        # further narrows which payments are returned.
        effective_start = max(contract_start, range_start)
        effective_end = min(contract_end, range_end)

        if effective_start > effective_end:
            continue

        payment_dates = _generate_contract_payment_dates(
            effective_start,
            effective_end,
            contract.payment_day,
        )

        for payment_date in payment_dates:
            totals_by_date[payment_date] += Decimal(contract.monthly_revenue)

    items = [
        {"payment_date": payment_date, "amount": amount}
        for payment_date, amount in sorted(totals_by_date.items())
    ]

    total_amount = sum((item["amount"] for item in items), Decimal("0.00"))
    total_payments = len(items)

    return items, total_amount, total_payments
