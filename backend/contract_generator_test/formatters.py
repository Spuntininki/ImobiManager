"""Presentation formatters for computed contract tokens.

These functions turn raw DB column values into the human-readable pt-BR
strings expected by the contract document template.

The implementations below are MOCKS — they return plausible-looking
output so the generator can be wired end-to-end. Replace each body with
the real formatting logic (number-to-words, full date, address join, etc.).
"""

from datetime import datetime
from decimal import Decimal

from app.models.address import Address


def monthly_revenue_desc(value: Decimal) -> str:
    """Write the monthly rent out in words, e.g. 'um mil e quinhentos'."""
    # TODO: real number-to-words in pt-BR
    return "um mil e quinhentos"


def deposit_months_desc(months: int) -> str:
    """Write the deposit duration in words, e.g. 'três meses de caução'."""
    # TODO: real number-to-words in pt-BR
    return "três meses de caução"


def contract_generate_date_desc(dt: datetime) -> str:
    """Format the generation date as a long pt-BR date, e.g. '14 de julho de 2026'."""
    # TODO: real pt-BR long-date formatting
    return "14 de julho de 2026"


def address_string(addr: Address) -> str:
    """Combine address fields into a single line, e.g. 'Rua das Flores, 123, Apto 45, Centro, São Paulo - SP, 01234-567'."""
    # TODO: real field joining with proper separators / fallbacks for None
    return "Rua das Flores, 123, Apto 45, Centro, São Paulo - SP, 01234-567"


def contract_time_desc(start: datetime, end: datetime) -> str:
    """Describe the rental duration, e.g. '12 (doze) meses'."""
    # TODO: compute months between start and end + number-to-words
    return "12 (doze) meses"