"""Business logic for the Contract resource (owner-scoped)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.models.contract import Contract
from app.models.enums import ContractStatus
from app.models.owner_renter import OwnerRenter
from app.schemas.contract import ContractCreate, ContractUpdate


class ContractRelationError(ValueError):
    """Raised when a (renter_id, owner_id) or (address_id, owner_id) relation
    is invalid. The endpoint catches ValueError and translates to 422.

    Kept as a ValueError subclass rather than a standalone exception to
    preserve the convention of "service raises ValueError → endpoint 422"
    established across the codebase.
    """


async def _validate_renter_belongs_to_owner(
    session: AsyncSession, owner_id: int, renter_id: int
) -> None:
    result = await session.execute(
        select(OwnerRenter).where(
            OwnerRenter.owner_id == owner_id,
            OwnerRenter.renter_id == renter_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise ContractRelationError(f"Renter {renter_id} is not linked to owner {owner_id}")


async def _validate_address_belongs_to_owner(
    session: AsyncSession, owner_id: int, address_id: int
) -> None:
    result = await session.execute(
        select(Address).where(Address.id == address_id, Address.owner_id == owner_id)
    )
    if result.scalar_one_or_none() is None:
        raise ContractRelationError(f"Address {address_id} does not belong to owner {owner_id}")


async def create_contract(
    session: AsyncSession, payload: ContractCreate, owner_id: int
) -> Contract:
    """Create a new contract. status defaults to PENDING. Validates that
    the renter and address are linked to the given owner.

    Raises ValueError (ContractRelationError) on relation violations;
    the endpoint is expected to catch and translate to 422.
    """
    await _validate_renter_belongs_to_owner(session, owner_id, payload.renter_id)
    await _validate_address_belongs_to_owner(session, owner_id, payload.address_id)
    contract = Contract(
        owner_id=owner_id,
        renter_id=payload.renter_id,
        address_id=payload.address_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        monthly_revenue=payload.monthly_revenue,
        deposit_value=payload.deposit_value,
        deposit_months=payload.deposit_months,
        status=ContractStatus.PENDING,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


async def get_contract(session: AsyncSession, contract_id: int) -> Contract | None:
    """Return a single contract by id, or None if not found."""
    result = await session.execute(select(Contract).where(Contract.id == contract_id))
    return result.scalar_one_or_none()


async def list_contracts_for_owner(session: AsyncSession, owner_id: int) -> list[Contract]:
    """Return contracts for the given owner, ordered by id."""
    result = await session.execute(
        select(Contract).where(Contract.owner_id == owner_id).order_by(Contract.id)
    )
    return list(result.scalars().all())


async def update_contract(
    session: AsyncSession,
    contract_id: int,
    payload: ContractUpdate,
    owner_id: int,
) -> Contract | None:
    """Patch a contract by id (partial update). Returns None if not found.

    If `renter_id` or `address_id` are present in the payload, re-validates
    the relationship to the contract's owner_id — same rule as create.
    Raises ValueError (ContractRelationError) on relation violations.
    """
    contract = await get_contract(session, contract_id)
    if contract is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    if "renter_id" in data and data["renter_id"] is not None:
        await _validate_renter_belongs_to_owner(session, contract.owner_id, data["renter_id"])
    if "address_id" in data and data["address_id"] is not None:
        await _validate_address_belongs_to_owner(session, contract.owner_id, data["address_id"])
    for field, value in data.items():
        if value is not None:
            setattr(contract, field, value)
    await session.commit()
    await session.refresh(contract)
    return contract


async def delete_contract(session: AsyncSession, contract_id: int) -> bool:
    """Delete a contract by id.

    Returns True if deleted, False if not found.
    """
    # TODO(phase future): replace physical delete with soft delete.
    contract = await get_contract(session, contract_id)
    if contract is None:
        return False
    await session.delete(contract)
    await session.commit()
    return True


__all__ = [
    "ContractRelationError",
    "create_contract",
    "get_contract",
    "list_contracts_for_owner",
    "update_contract",
    "delete_contract",
]
