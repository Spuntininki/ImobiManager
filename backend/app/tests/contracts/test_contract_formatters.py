"""Unit tests for the contract generation formatters.

These tests are deliberately DB-free: each formatter accepts an ORM-like
object by duck typing, so we feed it ``types.SimpleNamespace`` fakes with
just the attributes the formatter reads. This keeps the test fast (no session,
no fixtures) and pinned to formatter behavior rather than ORM plumbing.
"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.enums import DocumentType, PropertyType
from app.services.contract_generation.formatters import (
    _format_cpf,
    _format_date,
    _format_rg,
    address_string,
    contract_generate_date_desc,
    contract_time_desc,
    cooccupants,
    deposit_months_desc,
    end_date_desc,
    format_document,
    local_type_desc,
    monthly_revenue_desc,
    property_kind,
    purpose_usage,
    start_date_desc,
)

# --- factories ---------------------------------------------------------------


def _address(**overrides) -> SimpleNamespace:
    """A minimal address fake; callers override only what they exercise."""
    base = dict(
        street_name="Rua das Flores",
        number="123",
        complement=None,
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01234-567",
        type=PropertyType.HOUSE,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _contract(**overrides) -> SimpleNamespace:
    """A minimal contract fake; callers override only what they exercise."""
    base = dict(
        generation_date=datetime(2026, 7, 14, 10, 30),
        start_date=datetime(2026, 7, 1),
        end_date=datetime(2028, 7, 1),
        monthly_revenue=Decimal("1500.00"),
        deposit_months=3,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _document(doctype: DocumentType, value: str) -> SimpleNamespace:
    return SimpleNamespace(document_type=doctype, document=value)


# --- date formatters ---------------------------------------------------------


@pytest.mark.parametrize(
    "dt, expected",
    [
        (datetime(2026, 1, 1), "1 de janeiro de 2026"),
        (datetime(2026, 7, 14), "14 de julho de 2026"),
        (datetime(2024, 2, 29), "29 de fevereiro de 2024"),  # leap year
        (datetime(2026, 12, 31), "31 de dezembro de 2026"),
        (datetime(2027, 3, 1), "1 de março de 2027"),
    ],
)
def test_contract_generate_date_desc(dt: datetime, expected: str) -> None:
    contract = _contract(generation_date=dt)
    assert contract_generate_date_desc(contract) == expected


@pytest.mark.parametrize(
    "dt, expected",
    [
        (datetime(2026, 7, 1), "01/07/2026"),
        (datetime(2026, 12, 31), "31/12/2026"),
        (datetime(2026, 1, 9), "09/01/2026"),
        (datetime(2027, 2, 28), "28/02/2027"),
    ],
)
def test_format_date_helper(dt: datetime, expected: str) -> None:
    assert _format_date(dt) == expected


def test_start_date_desc() -> None:
    assert start_date_desc(_contract(start_date=datetime(2026, 7, 1))) == "01/07/2026"


def test_end_date_desc() -> None:
    assert end_date_desc(_contract(end_date=datetime(2028, 7, 1))) == "01/07/2028"


def test_contract_time_desc_same_year() -> None:
    contract = _contract(start_date=datetime(2026, 1, 1), end_date=datetime(2026, 12, 1))
    assert contract_time_desc(contract) == "11 (onze) meses"


def test_contract_time_desc_year_boundary() -> None:
    contract = _contract(start_date=datetime(2026, 7, 1), end_date=datetime(2028, 7, 1))
    assert contract_time_desc(contract) == "24 (vinte e quatro) meses"


def test_contract_time_desc_zero_months() -> None:
    contract = _contract(start_date=datetime(2026, 7, 1), end_date=datetime(2026, 7, 1))
    assert contract_time_desc(contract) == "0 (zero) meses"


def test_contract_time_desc_multi_year_span() -> None:
    contract = _contract(start_date=datetime(2026, 6, 15), end_date=datetime(2031, 3, 20))
    # (2031-2026)*12 + (3-6) = 60 - 3 = 57
    assert contract_time_desc(contract) == "57 (cinquenta e sete) meses"


# --- address formatters ------------------------------------------------------


def test_address_string_without_complement() -> None:
    assert address_string(_address()) == "Rua das Flores, 123, Centro, São Paulo - SP, 01234-567"


def test_address_string_with_complement() -> None:
    addr = _address(complement="Apto 45")
    assert address_string(addr) == "Rua das Flores, 123, Apto 45, Centro, São Paulo - SP, 01234-567"


def test_address_string_empty_complement_omitted() -> None:
    # Empty string is falsy → complement branch skipped, same as None.
    addr = _address(complement="")
    assert address_string(addr) == "Rua das Flores, 123, Centro, São Paulo - SP, 01234-567"


# --- property-type phrase formatters -----------------------------------------


def test_local_type_desc_house() -> None:
    assert local_type_desc(_address(type=PropertyType.HOUSE)) == "residencial"


def test_local_type_desc_commercial() -> None:
    assert local_type_desc(_address(type=PropertyType.COMMERCIAL)) == "comercial"


def test_property_kind_house() -> None:
    assert property_kind(_address(type=PropertyType.HOUSE)) == "uma casa"


def test_property_kind_commercial() -> None:
    assert property_kind(_address(type=PropertyType.COMMERCIAL)) == "um ponto comercial"


def test_purpose_usage_house() -> None:
    assert purpose_usage(_address(type=PropertyType.HOUSE)) == "como residência e domicílio"


def test_purpose_usage_commercial() -> None:
    assert purpose_usage(_address(type=PropertyType.COMMERCIAL)) == "para fins comerciais"


def test_cooccupants_house() -> None:
    assert cooccupants(_address(type=PropertyType.HOUSE)) == "familiares"


def test_cooccupants_commercial() -> None:
    assert cooccupants(_address(type=PropertyType.COMMERCIAL)) == "funcionários"


# --- number-to-words formatters ----------------------------------------------


@pytest.mark.parametrize(
    "months, expected",
    [
        (1, "um meses"),  # note: grammar fix-up tracked separately, formatter just joins
        (2, "dois meses"),
        (3, "três meses"),
        (12, "doze meses"),
        (6, "seis meses"),
    ],
)
def test_deposit_months_desc(months: int, expected: str) -> None:
    assert deposit_months_desc(_contract(deposit_months=months)) == expected


def test_monthly_revenue_desc_whole() -> None:
    assert monthly_revenue_desc(_contract(monthly_revenue=Decimal("1500.00"))) == "mil e quinhentos"


def test_monthly_revenue_desc_truncates_cents() -> None:
    # Decimal cents are dropped via int() per design.
    assert monthly_revenue_desc(_contract(monthly_revenue=Decimal("1500.50"))) == "mil e quinhentos"


def test_monthly_revenue_desc_zero() -> None:
    assert monthly_revenue_desc(_contract(monthly_revenue=Decimal("0.00"))) == "zero"


def test_monthly_revenue_desc_large() -> None:
    assert (
        monthly_revenue_desc(_contract(monthly_revenue=Decimal("52500.00")))
        == "cinquenta e dois mil e quinhentos"
    )


# --- document formatters -----------------------------------------------------


def test_format_cpf_raw_digits() -> None:
    assert _format_cpf("12345678901") == "123.456.789-01"


def test_format_cpf_already_masked() -> None:
    assert _format_cpf("123.456.789-01") == "123.456.789-01"


def test_format_cpf_wrong_length_returned_unchanged() -> None:
    assert _format_cpf("1234567890") == "1234567890"  # 10 digits


def test_format_cpf_empty() -> None:
    assert _format_cpf("") == ""


def test_format_rg_nine_digits() -> None:
    assert _format_rg("266196408") == "26.619.640-8"


def test_format_rg_eight_digits() -> None:
    assert _format_rg("12345678") == "1.234.567-8"


def test_format_rg_already_masked_nine() -> None:
    assert _format_rg("26.619.640-8") == "26.619.640-8"


def test_format_rg_wrong_length_returned_unchanged() -> None:
    assert _format_rg("123456") == "123456"  # 6 digits


def test_format_document_cpf() -> None:
    doc = _document(DocumentType.CPF, "77327189092")
    assert format_document(doc) == "773.271.890-92"


def test_format_document_rg_eight_digits() -> None:
    doc = _document(DocumentType.RG, "112000757")
    assert format_document(doc) == "11.200.075-7"


def test_format_document_unknown_type_raises() -> None:
    # Simulate a document type the formatters don't handle (e.g. CNPJ today).
    doc = SimpleNamespace(document_type=DocumentType.CNPJ, document="12345678000199")
    with pytest.raises(ValueError, match="No document formatter"):
        format_document(doc)
