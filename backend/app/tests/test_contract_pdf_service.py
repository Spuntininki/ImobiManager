"""Unit tests for the contract PDF pipeline orchestrator.

Focus is on ``_fill_tokens`` — the pure substitution step. It is exercised
with ``SimpleNamespace`` fakes so no DB session is required. The fetch and
render halves are covered by other test modules (renderer) and the upcoming
endpoint integration tests; here we lock in the dispatch + substitution
behavior in isolation.
"""

import re
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.models.enums import DocumentType, PropertyType
from app.services.contract_generation.default_template import load_default_content
from app.services.contract_pdf_service import FORMATTERS, _fill_tokens

# --- fakes ------------------------------------------------------------------


def _owner() -> SimpleNamespace:
    return SimpleNamespace(name="Laurindo Figueiredo")


def _renter() -> SimpleNamespace:
    return SimpleNamespace(name="Teste")


def _address() -> SimpleNamespace:
    return SimpleNamespace(
        street_name="Rua das Flores",
        number="123",
        complement=None,
        neighborhood="Centro",
        city="São Paulo",
        state="SP",
        zip_code="01234-567",
        type=PropertyType.HOUSE,
    )


def _contract() -> SimpleNamespace:
    return SimpleNamespace(
        generation_date=datetime(2026, 7, 14, 10, 30),
        start_date=datetime(2026, 7, 1),
        end_date=datetime(2028, 7, 1),
        monthly_revenue=Decimal("1500.00"),
        deposit_months=3,
        payment_day=5,
    )


def _document(doctype: DocumentType, value: str) -> SimpleNamespace:
    return SimpleNamespace(document_type=doctype, document=value)


def _contract_data() -> dict:
    """The dict shape that ``_fetch_contract_data`` produces."""
    return {
        "contracts": _contract(),
        "owners": _owner(),
        "renters": _renter(),
        "addresses": _address(),
        "owner_documents": {
            "CPF": _document(DocumentType.CPF, "77327189092"),
            "RG": _document(DocumentType.RG, "266196408"),
        },
        "renter_documents": {
            "CPF": _document(DocumentType.CPF, "25349726005"),
            "RG": _document(DocumentType.RG, "112000757"),
        },
    }


# --- happy path: end-to-end fill against the real default template ----------


def test_fill_tokens_with_default_template_substitutes_all_tokens() -> None:
    """Run the full default template against the fake contract_data dict and
    assert no ``<REPLACE>`` placeholder survives in the rendered lines.
    """
    template = load_default_content()
    converted = _fill_tokens(template, _contract_data())

    # Every section produced the expected type and non-empty lines.
    assert converted["title_lines"]["type"] == "title"
    assert converted["content_lines"]["type"] == "paragh"
    assert converted["sign_lines"]["type"] == "sign"

    # No token placeholder leaked through.
    pattern = re.compile(r"<REPLACE>(.*?)</REPLACE>")
    for section in converted.values():
        for line in section["lines"]:
            if isinstance(line, list):
                for item in line:
                    assert pattern.findall(item) == [], f"Unfilled token in sign line: {item}"
            else:
                assert pattern.findall(line) == [], f"Unfilled token in line: {line}"


def test_fill_tokens_does_not_mutate_input_template() -> None:
    """The service must not mutate the row loaded from the DB — copy first."""
    template = load_default_content()
    snapshot_before = {
        token: dict(entry) for token, entry in template["replace"].items()
    }
    _fill_tokens(template, _contract_data())
    # The original template's replace entries have no "value" key still.
    for token, entry in template["replace"].items():
        assert "value" not in entry, f"Template row mutated for token {token!r}"
        assert dict(entry) == snapshot_before[token]


# --- specific tokens land correctly in the rendered lines ------------------


def test_fill_tokens_owner_line_includes_masked_cpf_and_rg() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    owner_line = converted["content_lines"]["lines"][0]
    assert "Laurindo Figueiredo" in owner_line
    assert "773.271.890-92" in owner_line  # CPF masked
    assert "26.619.640-8" in owner_line  # RG masked


def test_fill_tokens_renter_line_includes_masked_cpf_and_rg() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    renter_line = converted["content_lines"]["lines"][1]
    assert "Teste" in renter_line
    assert "253.497.260-05" in renter_line
    assert "11.200.075-7" in renter_line


def test_fill_tokens_uses_property_phrases_for_house() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    # The cession clause (3rd line, index 3) toggles on property type.
    cession_line = converted["content_lines"]["lines"][3]
    assert "residencial" in cession_line
    assert "uma casa" in cession_line
    assert "como residência e domicílio" in cession_line


def test_fill_tokens_uses_property_phrases_for_commercial() -> None:
    data = _contract_data()
    data["addresses"] = SimpleNamespace(
        **{**vars(_address()), "type": PropertyType.COMMERCIAL}
    )
    converted = _fill_tokens(load_default_content(), data)
    cession_line = converted["content_lines"]["lines"][3]
    assert "comercial" in cession_line
    assert "um ponto comercial" in cession_line
    assert "para fins comerciais" in cession_line


def test_fill_tokens_renders_dates_as_dd_mm_yyyy() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    # The contract-time clause (4th line) carries start and end dates.
    time_line = converted["content_lines"]["lines"][4]
    assert "01/07/2026" in time_line
    assert "01/07/2028" in time_line
    # Computed month count (24 months for a 2-year span).
    assert "24 (vinte e quatro) meses" in time_line


def test_fill_tokens_renders_monthly_revenue_with_decimal_and_words() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    # The rent clause (5th line) carries both decimal and words tokens.
    rent_line = converted["content_lines"]["lines"][5]
    assert "1500.00" in rent_line  # non-computed: raw decimal getattr
    assert "mil e quinhentos" in rent_line  # computed: num2words


def test_fill_tokens_sign_block_substitutes_owner_and_renter_names() -> None:
    converted = _fill_tokens(load_default_content(), _contract_data())
    # Last sign row holds the names.
    sign_lines = converted["sign_lines"]["lines"]
    assert sign_lines[-1] == ["Laurindo Figueiredo", "Teste"]


# --- FORMATTERS registry sanity --------------------------------------------


def test_every_computed_token_in_default_template_has_a_formatter() -> None:
    """Guard against drift: every token marked computed in the seed must
    have an entry in the service's FORMATTERS registry.
    """
    template = load_default_content()
    for token, entry in template["replace"].items():
        if entry.get("computed"):
            assert token in FORMATTERS, f"Missing formatter for computed token {token!r}"
