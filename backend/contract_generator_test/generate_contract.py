import asyncio
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import aliased

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from formatters import (  # noqa: E402
    address_string,
    contract_generate_date_desc,
    contract_time_desc,
    deposit_months_desc,
    end_date_desc,
    format_document,
    local_type_desc,
    monthly_revenue_desc,
    start_date_desc,
)
from render_pdf import render  # noqa: E402

from app.db.session import async_session_factory  # noqa: E402
from app.models.address import Address  # noqa: E402
from app.models.contract import Contract  # noqa: E402
from app.models.enums import DocumentType  # noqa: E402
from app.models.owner import Owner  # noqa: E402
from app.models.owner_document import OwnerDocument  # noqa: E402
from app.models.renter import Renter  # noqa: E402
from app.models.renter_document import RenterDocument  # noqa: E402


async def query_the_contract_data(contract_id: int) -> dict:
    """Query a contract with all related tables in a single join, returning
    a dict keyed by table name so token lookups stay O(1).

    Document tables are nested sub-dicts keyed by ``document_type`` because
    the same table is joined once per type (CPF, RG).
    """
    OwnerDocCPF = aliased(OwnerDocument)
    OwnerDocRG = aliased(OwnerDocument)
    RenterDocCPF = aliased(RenterDocument)
    RenterDocRG = aliased(RenterDocument)

    async with async_session_factory() as session:
        stmt = (
            select(Contract, Owner, Renter, Address,
                OwnerDocCPF, OwnerDocRG, RenterDocCPF, RenterDocRG)
            .join(Owner, Contract.owner_id == Owner.id)
            .join(Renter, Contract.renter_id == Renter.id)
            .join(Address, Contract.address_id == Address.id)
            .outerjoin(OwnerDocCPF, (OwnerDocCPF.owner_id == Owner.id) & (OwnerDocCPF.document_type == DocumentType.CPF))
            .outerjoin(OwnerDocRG,  (OwnerDocRG.owner_id == Owner.id)  & (OwnerDocRG.document_type == DocumentType.RG))
            .outerjoin(RenterDocCPF,(RenterDocCPF.renter_id == Renter.id)& (RenterDocCPF.document_type == DocumentType.CPF))
            .outerjoin(RenterDocRG, (RenterDocRG.renter_id == Renter.id) & (RenterDocRG.document_type == DocumentType.RG))
            .where(Contract.id == contract_id)
        )
        result = await session.execute(stmt)
        row = result.one()

    contract, owner, renter, address, owner_cpf_doc, owner_rg_doc, renter_cpf_doc, renter_rg_doc = row

    if owner_cpf_doc is None:
        raise Exception("Error: owner_cpf is null")
    if owner_rg_doc is None:
        raise Exception("Error: owner_rg is null")
    if renter_cpf_doc is None:
        raise Exception("Error: renter_cpf is null")
    if renter_rg_doc is None:
        raise Exception("Error: renter_rg is null")
    return {
        "contracts": contract,
        "owners": owner,
        "renters": renter,
        "addresses": address,
        "owner_documents": {"CPF": owner_cpf_doc, "RG": owner_rg_doc},
        "renter_documents": {"CPF": renter_cpf_doc, "RG": renter_rg_doc},
    }


async def main() -> None:
    """Load doc_content.json and demonstrate a database query."""
    doc_path = Path(__file__).resolve().parent / "doc_content.json"
    with doc_path.open("r", encoding="utf-8") as arquivo:
        data = json.load(arquivo)

    CONTRACT_ID_TO_PROCESS = 2

    FORMATTERS = {
        "owner_cpf": format_document,
        "owner_rg": format_document,
        "renter_cpf": format_document,
        "renter_rg": format_document,
        "contract_time_string_desc": contract_time_desc,
        "address_string": address_string,
        "monthly_revenue_string_desc": monthly_revenue_desc,
        "deposit_months_string_desc": deposit_months_desc,
        "contract_generate_date_description": contract_generate_date_desc,
        "start_date_string": start_date_desc,
        "end_date_string": end_date_desc,
        "local_type": local_type_desc,
    }

    contract_data = await query_the_contract_data(contract_id=CONTRACT_ID_TO_PROCESS)

    for description, value in data["replace"].items():
        model_obj = (contract_data[value["table"]][value["document_type"]]
                     if isinstance(contract_data[value["table"]], dict)
                     else contract_data[value["table"]])

        if value.get("computed"):
            value["value"] = FORMATTERS[description](model_obj)
        else:
            value["value"] = getattr(model_obj, value["colum"])

    del contract_data

    COMPILED_PATTERN = re.compile(r"<REPLACE>(.*?)</REPLACE>")

    def replacer(match: re.Match) -> str:
        token = match.group(1)
        return str(data["replace"][token]["value"])
    converted_data = {}
    for content_desc, content_lines in data["content"].items():
        print(f"\n[{content_desc}]")
        converted_data[content_desc] = {
            "lines": [],
            "type": ''
        }
        for line in content_lines["lines"]:
            if isinstance(line, list):
                filled = [COMPILED_PATTERN.sub(replacer, item) for item in line]
                converted_data[content_desc]['lines'].append(filled)
                converted_data[content_desc]['type'] = content_lines['type']
            else:
                filled = COMPILED_PATTERN.sub(replacer, line)
                converted_data[content_desc]['lines'].append(filled)
                converted_data[content_desc]['type'] = content_lines['type']
    print(converted_data)

    style_path = Path(__file__).resolve().parent / "doc_style.json"
    with style_path.open("r", encoding="utf-8") as arquivo:
        style_config = json.load(arquivo)

    output_path = Path(__file__).resolve().parent / "contract.pdf"
    render(converted_data, style_config, output_path)
    print(f"\nPDF generated: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
