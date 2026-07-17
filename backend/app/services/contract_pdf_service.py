"""Contract PDF generation pipeline — orchestrates fetch + fill + render.

Composes the pieces from the ``contract_generation`` package (see its
docstring for the pipeline overview) against an injected ``AsyncSession``.
``generate_contract_pdf`` is the public entrypoint; ``build_contract_pdf_filename``
builds the download filename (renter-name → ASCII slug + contract id).
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.filenames import to_ascii_filename_slug
from app.models.address import Address
from app.models.contract import Contract
from app.models.contract_template import ContractTemplate
from app.models.enums import DocumentType
from app.models.owner import Owner
from app.models.owner_document import OwnerDocument
from app.models.renter import Renter
from app.models.renter_document import RenterDocument
from app.services.contract_generation import formatters
from app.services.contract_generation.renderer import render
from app.services.contract_generation.validation import (
    TOKEN_RE,
    ContractNotFoundError,
    validate_template,
)

# Portuguese name connector particles — dropped so the contract PDF filename
# keeps the first two *names* (e.g. "João da Silva" → "Joao_Silva", not
# "Joao_da"). Lives here because this is a renter-name presentation rule.
_NAME_CONNECTORS = frozenset({"da", "de", "do", "das", "dos", "e"})

# Token → formatter dispatch table. JSON decides routing via the ``computed``
# flag; this dict is the single place that knows which Python function handles
# each computed token. Adding a token = +1 entry here + +1 entry in the seed.
FORMATTERS = {
    "owner_cpf": formatters.format_document,
    "owner_rg": formatters.format_document,
    "renter_cpf": formatters.format_document,
    "renter_rg": formatters.format_document,
    "contract_time_string_desc": formatters.contract_time_desc,
    "address_string": formatters.address_string,
    "monthly_revenue_string_desc": formatters.monthly_revenue_desc,
    "deposit_months_string_desc": formatters.deposit_months_desc,
    "contract_generate_date_description": formatters.contract_generate_date_desc,
    "start_date_string": formatters.start_date_desc,
    "end_date_string": formatters.end_date_desc,
    "local_type": formatters.local_type_desc,
    "property_kind": formatters.property_kind,
    "purpose_usage": formatters.purpose_usage,
    "cooccupants": formatters.cooccupants,
}

async def _fetch_contract_data(session: AsyncSession, contract_id: int) -> dict:
    """Load a contract + all related rows in a single join.

    Returns a dict keyed by table name so token lookup stays O(1). Document
    tables are nested sub-dicts keyed by ``document_type`` (CPF / RG) because
    the same table is joined once per type.

    Raises ``ContractNotFoundError`` if the contract does not exist — the
    endpoint translates that to 404.
    """
    OwnerDocCPF = aliased(OwnerDocument)
    OwnerDocRG = aliased(OwnerDocument)
    RenterDocCPF = aliased(RenterDocument)
    RenterDocRG = aliased(RenterDocument)

    stmt = (
        select(Contract, Owner, Renter, Address, OwnerDocCPF, OwnerDocRG, RenterDocCPF, RenterDocRG)
        .join(Owner, Contract.owner_id == Owner.id)
        .join(Renter, Contract.renter_id == Renter.id)
        .join(Address, Contract.address_id == Address.id)
        .outerjoin(
            OwnerDocCPF,
            (OwnerDocCPF.owner_id == Owner.id) & (OwnerDocCPF.document_type == DocumentType.CPF),
        )
        .outerjoin(
            OwnerDocRG,
            (OwnerDocRG.owner_id == Owner.id) & (OwnerDocRG.document_type == DocumentType.RG),
        )
        .outerjoin(
            RenterDocCPF,
            (RenterDocCPF.renter_id == Renter.id)
            & (RenterDocCPF.document_type == DocumentType.CPF),
        )
        .outerjoin(
            RenterDocRG,
            (RenterDocRG.renter_id == Renter.id) & (RenterDocRG.document_type == DocumentType.RG),
        )
        .where(Contract.id == contract_id)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row is None:
        raise ContractNotFoundError(f"Contract {contract_id} not found")

    (
        contract,
        owner,
        renter,
        address,
        owner_cpf_doc,
        owner_rg_doc,
        renter_cpf_doc,
        renter_rg_doc,
    ) = row

    # Document rows are OUTER JOINed so the contract still loads when a
    # document is absent. The expected contract has both CPF and RG for
    # both parties; raise explicitly so the rendered PDF never silently
    # substitutes ``None`` for a CPF/RG mask.
    missing = [
        name
        for name, doc in (
            ("owner_cpf", owner_cpf_doc),
            ("owner_rg", owner_rg_doc),
            ("renter_cpf", renter_cpf_doc),
            ("renter_rg", renter_rg_doc),
        )
        if doc is None
    ]
    if missing:
        raise ValueError(f"Missing required document(s): {', '.join(missing)}")

    return {
        "contracts": contract,
        "owners": owner,
        "renters": renter,
        "addresses": address,
        "owner_documents": {"CPF": owner_cpf_doc, "RG": owner_rg_doc},
        "renter_documents": {"CPF": renter_cpf_doc, "RG": renter_rg_doc},
    }


def _fill_tokens(template: dict, contract_data: dict) -> dict:
    """Substitute template tokens with values from ``contract_data``.

    Walks the template's ``replace`` entries once, dispatching each to a
    registered formatter (``computed`` token) or a plain ``getattr``
    (pass-through token). Then walks the section lines, replacing every
    ``<REPLACE>token</REPLACE>`` with its resolved value, producing
    ``converted_data`` ready for the renderer.

    Pure: no I/O, no side effects on the inputs (the template dict is copied
    before mutation so the caller's template row stays pristine).
    """
    working = {
        "content": template["content"],
        "replace": {token: dict(entry) for token, entry in template["replace"].items()},
    }

    for token, entry in working["replace"].items():
        table = entry["table"]
        target = contract_data[table]
        if isinstance(target, dict):
            # Document tables are nested dicts keyed by document_type.
            model_obj = target[entry["document_type"]]
        else:
            model_obj = target

        if entry.get("computed"):
            entry["value"] = FORMATTERS[token](model_obj)
        else:
            entry["value"] = getattr(model_obj, entry["colum"])

    def replacer(match: re.Match) -> str:
        return str(working["replace"][match.group(1)]["value"])

    converted_data: dict = {}
    for section_name, section in working["content"].items():
        lines: list = []
        for line in section["lines"]:
            if isinstance(line, list):
                lines.append([TOKEN_RE.sub(replacer, item) for item in line])
            else:
                lines.append(TOKEN_RE.sub(replacer, line))
        converted_data[section_name] = {"lines": lines, "type": section["type"]}
    return converted_data


async def generate_contract_pdf(
    session: AsyncSession,
    contract_id: int,
    template_code: str = "standard",
) -> bytes:
    """Generate a contract PDF and return it as bytes.

    Pipeline: load template row → validate against FORMATTERS → fetch the
    contract join → fill tokens → render to PDF bytes.

    Raises:
        ValueError: if the template row is missing/inactive or a required
            document is absent on the contract.
        ContractNotFoundError: if ``contract_id`` does not exist.
    """
    template_row = await session.scalar(
        select(ContractTemplate).where(
            ContractTemplate.code == template_code,
            ContractTemplate.is_active.is_(True),
        )
    )
    if template_row is None:
        raise ValueError(f"No active contract template with code {template_code!r}")

    # Fail loud before any DB join if the template references tokens we
    # don't have formatters for — prevents silent <REPLACE>…</REPLACE>
    # leakage into a generated PDF.
    validate_template(template_row.content, FORMATTERS)

    contract_data = await _fetch_contract_data(session, contract_id)
    converted_data = _fill_tokens(template_row.content, contract_data)
    return render(converted_data, template_row.style)


def build_contract_pdf_filename(renter_name: str | None, contract_id: int) -> str:
    """Build the download filename for a contract PDF.

    Reduces ``renter_name`` to its first two non-connector tokens (so
    "João da Silva" → "Joao_Silva", dropping the pt-BR particle "da"),
    deburrs accents to ASCII via ``to_ascii_filename_slug``, and combines
    with the contract id for uniqueness: ``Contrato-<slug>-<contract_id>.pdf``.
    Falls back to ``Contrato-renter-<contract_id>.pdf`` when the name has no
    usable tokens (defensive only — the DB enforces non-empty names).
    """
    tokens = [t for t in (renter_name or "").split() if t.lower() not in _NAME_CONNECTORS][:2]
    slug = to_ascii_filename_slug(" ".join(tokens))
    name_part = slug or "renter"
    return f"Contrato-{name_part}-{contract_id}.pdf"
