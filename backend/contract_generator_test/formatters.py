"""Presentation formatters for computed contract tokens.

Each formatter receives the ORM model object that owns the source column(s)
declared for the token in ``doc_content.json`` (Option A: model-in). The
formatter is responsible for reading whatever columns it needs and turning
them into the human-readable pt-BR string expected by the contract document
template. Passing the whole model keeps the dispatch site in
``generate_contract.py`` uniform — a single ``FORMATTERS[token](model_obj)``
call — regardless of how many columns a formatter consumes.
"""

import re
from datetime import datetime

from num2words import num2words

from app.models.address import Address
from app.models.contract import Contract
from app.models.enums import DocumentType, PropertyType
from app.models.owner_document import OwnerDocument
from app.models.renter_document import RenterDocument

# pt-BR long-form month names, indexed 1..12 (index 0 is unused).
_MONTHS_PT_BR = (
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def contract_generate_date_desc(contract: Contract) -> str:
    """Format the generation date as a long pt-BR date, e.g. '14 de julho de 2026'.

    Source columns: ``contracts.generation_date``.
    """
    dt = contract.generation_date
    return f"{dt.day} de {_MONTHS_PT_BR[dt.month]} de {dt.year}"


def address_string(address: Address) -> str:
    """Combine address fields into a single line.

    Example: 'Rua das Flores, 123, Apto 45, Centro, São Paulo - SP, 01234-567'.
    ``complement`` is optional — when ``None`` it is omitted and no dangling
    separator is left behind.
    """
    street = f"{address.street_name}, {address.number}"
    if address.complement:
        street = f"{street}, {address.complement}"
    return f"{street}, {address.neighborhood}, {address.city} - {address.state}, {address.zip_code}"


def local_type_desc(address: Address) -> str:
    """Translate the property type to lowercase pt-BR: 'residencial' / 'comercial'.

    Source columns: ``addresses.type`` (a ``PropertyType`` enum). The raw enum
    values (``HOUSE`` / ``COMMERCIAL``) are internal English identifiers and
    never appear in the contract text — this formatter is the single source
    of truth for the pt-BR wording.
    """
    return _property_phrase(address, "residencial", "comercial")


def _property_phrase(address: Address, house: str, commercial: str) -> str:
    """Shared helper: return ``house`` or ``commercial`` based on property type.

    Centralizes the ``match``/``case`` on ``PropertyType`` so every
    property-type-dependent phrase token dispatches the same way; adding a
    future ``PropertyType`` value (e.g. ``RURAL``) is one new ``case`` here,
    not one per phrase formatter.
    """
    match address.type:
        case PropertyType.HOUSE:
            return house
        case PropertyType.COMMERCIAL:
            return commercial


def property_kind(address: Address) -> str:
    """Noun for the rented unit: 'uma casa' / 'um ponto comercial'.

    Source columns: ``addresses.type``. Used where the contract describes the
    ceded property ('cede ... uma casa, na ...').
    """
    return _property_phrase(address, "uma casa", "um ponto comercial")


def purpose_usage(address: Address) -> str:
    """Destination-usage phrase: 'como residência e domicílio' / 'para fins comerciais'.

    Source columns: ``addresses.type``. Reused on two template lines (the cession
    clause and the exclusive-use clause) so both flip together when the
    property type changes — the destination wording can never contradict the
    ``local_type`` token earlier in the same sentence.
    """
    return _property_phrase(address, "como residência e domicílio", "para fins comerciais")


def cooccupants(address: Address) -> str:
    """Who occupies the premises alongside the tenant: 'familiares' / 'funcionários'.

    Source columns: ``addresses.type``. A commercial tenant (a company) has
    'funcionários' rather than 'familiares'.
    """
    return _property_phrase(address, "familiares", "funcionários")


def deposit_months_desc(contract: Contract) -> str:
    """Write the deposit duration in words, e.g. 'três meses'.

    Source columns: ``contracts.deposit_months``.
    """
    return f"{num2words(contract.deposit_months, lang='pt_BR')} meses"


def monthly_revenue_desc(contract: Contract) -> str:
    """Write the monthly rent out in words, e.g. 'mil e quinhentos'.

    Source columns: ``contracts.monthly_revenue``. Cents are intentionally
    truncated — the template appends 'reais' separately and never mentions
    centavos.
    """
    return num2words(int(contract.monthly_revenue), lang='pt_BR')


def contract_time_desc(contract: Contract) -> str:
    """Describe the rental duration, e.g. '12 (doze) meses'.

    Source columns: ``contracts.start_date`` and ``contracts.end_date``
    (this formatter consumes two columns, which is why it receives the whole
    model rather than a single scalar). The duration is computed in whole
    months from the year/month of the two dates.
    """
    months = (contract.end_date.year - contract.start_date.year) * 12 + (
        contract.end_date.month - contract.start_date.month
    )
    return f"{months} ({num2words(months, lang='pt_BR')}) meses"


def _format_date(dt: datetime) -> str:
    """Format a datetime as ``DD/MM/YYYY`` (date part only)."""
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year:04d}"


def start_date_desc(contract: Contract) -> str:
    """Format the contract start date as ``DD/MM/YYYY``.

    Source columns: ``contracts.start_date``.
    """
    return _format_date(contract.start_date)


def end_date_desc(contract: Contract) -> str:
    """Format the contract end date as ``DD/MM/YYYY``.

    Source columns: ``contracts.end_date``.
    """
    return _format_date(contract.end_date)


"""Document formatters.

Brazilian legal documents (CPF/RG) are stored as raw digit strings in the DB
but must be rendered with their canonical masks in the contract text. A single
``format_document`` dispatches on ``document_type`` so all four document tokens
(owner_cpf/owner_rg/renter_cpf/renter_rg) share one function instead of four
near-identical wrappers — owner-CPF and renter-CPF format identically once the
model object is in hand.
"""

_NON_DIGITS = re.compile(r"\D")


def _format_cpf(value: str) -> str:
    """Mask a CPF as ``###.###.###-##`` (expects 11 digits).

    Non-digits are stripped first so the function is robust whether the DB
    stores the raw ``"12345678901"`` or a pre-formatted ``"123.456.789-01"``.
    If the cleaned length is not 11 the original value is returned unchanged
    rather than emitting a misaligned mask.
    """
    digits = _NON_DIGITS.sub("", value)
    if len(digits) != 11:
        return value
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _format_rg(value: str) -> str:
    """Mask an RG with a generic layout (state-agnostic).

    Brazilian RGs vary by issuing state, so a single canonical mask cannot fit
    every case. The two most common digit counts are handled:

    * 9 digits → ``##.###.###-#``
    * 8 digits → ``#.###.###-#``

    Any other length returns the original value unchanged.
    """
    digits = _NON_DIGITS.sub("", value)
    if len(digits) == 9:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}-{digits[8]}"
    if len(digits) == 8:
        return f"{digits[0]}.{digits[1:4]}.{digits[4:7]}-{digits[7]}"
    return value


def format_document(doc: OwnerDocument | RenterDocument) -> str:
    """Format a legal document (CPF/RG) according to its ``document_type``.

    Dispatches internally on ``doc.document_type``; the token name in the
    JSON only selects *which* aliased row to fetch — once the model object is
    in hand, the mask depends solely on the document type, not on whose
    document it is (owner vs. renter).
    """
    match doc.document_type:
        case DocumentType.CPF:
            return _format_cpf(doc.document)
        case DocumentType.RG:
            return _format_rg(doc.document)
        case _:
            raise ValueError(
                f"No document formatter for type {doc.document_type!r}"
            )
