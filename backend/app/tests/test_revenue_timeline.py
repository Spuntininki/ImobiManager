"""Tests for the owner revenue timeline endpoint."""

from datetime import date, datetime
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.address import Address
from app.models.contract import Contract
from app.models.owner import Owner
from app.models.owner_renter import OwnerRenter
from app.models.renter import Renter
from app.models.user import User
from app.models.user_owner import UserOwner


async def _create_user(
    session: AsyncSession, email: str = "user@test.com", password: str = "secret"
) -> User:
    user = User(email=email, name="Test User", password=hash_password(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _auth_headers(
    client: AsyncClient, email: str = "user@test.com", password: str = "secret"
) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_owner(
    session: AsyncSession, user: User, name: str = "Owner One"
) -> Owner:
    owner = Owner(name=name)
    session.add(owner)
    await session.flush()
    session.add(UserOwner(user_id=user.id, owner_id=owner.id))
    await session.commit()
    await session.refresh(owner)
    return owner


async def _create_renter(session: AsyncSession, owner: Owner, name: str = "Maria") -> Renter:
    renter = Renter(name=name, primary_contact="999")
    session.add(renter)
    await session.flush()
    session.add(OwnerRenter(owner_id=owner.id, renter_id=renter.id))
    await session.commit()
    await session.refresh(renter)
    return renter


async def _create_address(session: AsyncSession, owner: Owner) -> Address:
    address = Address(
        owner_id=owner.id,
        street_name="Rua X",
        number="1",
        neighborhood="B",
        city="C",
        state="SP",
        zip_code="00000-000",
        type="HOUSE",
    )
    session.add(address)
    await session.commit()
    await session.refresh(address)
    return address


async def _create_contract(
    session: AsyncSession,
    owner: Owner,
    renter: Renter,
    address: Address,
    start_date: date,
    end_date: date,
    monthly_revenue: Decimal,
    payment_day: int,
    status: str,
) -> Contract:
    contract = Contract(
        owner_id=owner.id,
        renter_id=renter.id,
        address_id=address.id,
        start_date=datetime(start_date.year, start_date.month, start_date.day),
        end_date=datetime(end_date.year, end_date.month, end_date.day),
        monthly_revenue=monthly_revenue,
        deposit_value=Decimal("0.00"),
        deposit_months=0,
        payment_day=payment_day,
        status=status,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)
    return contract


# --- Auth / scoping ---


async def test_revenue_timeline_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/owners/1/revenue-timeline")
    assert response.status_code == 401


async def test_revenue_timeline_for_unmanaged_owner_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    other = Owner(name="Someone Elses")
    db_session.add(other)
    await db_session.commit()
    response = await client.get(
        f"/api/v1/owners/{other.id}/revenue-timeline", headers=headers
    )
    assert response.status_code == 404


# --- Timeline generation ---


async def test_revenue_timeline_active_contract(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    owner = await _create_owner(db_session, user)
    renter = await _create_renter(db_session, owner)
    address = await _create_address(db_session, owner)

    today = date.today()
    start = today.replace(day=1)
    end = (today.replace(year=today.year + 1)).replace(day=1)
    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="ACTIVE",
    )

    response = await client.get(
        f"/api/v1/owners/{owner.id}/revenue-timeline?start_date={start}&end_date={end}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 12
    assert all(item["amount"] == "1000.00" for item in data)
    assert data[0]["payment_date"] == start.replace(day=5).isoformat()


async def test_revenue_timeline_aggregates_multiple_contracts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    owner = await _create_owner(db_session, user)
    renter = await _create_renter(db_session, owner)
    address = await _create_address(db_session, owner)

    today = date.today()
    start = today.replace(day=1)
    end = (today.replace(year=today.year + 1)).replace(day=1)

    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="ACTIVE",
    )
    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("500.00"),
        payment_day=5,
        status="ACTIVE",
    )

    response = await client.get(
        f"/api/v1/owners/{owner.id}/revenue-timeline?start_date={start}&end_date={end}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["amount"] == "1500.00" for item in data)


async def test_revenue_timeline_excludes_non_active_contracts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    owner = await _create_owner(db_session, user)
    renter = await _create_renter(db_session, owner)
    address = await _create_address(db_session, owner)

    today = date.today()
    start = today.replace(day=1)
    end = (today.replace(year=today.year + 1)).replace(day=1)

    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="PENDING",
    )
    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="CANCELLED",
    )

    response = await client.get(
        f"/api/v1/owners/{owner.id}/revenue-timeline?start_date={start}&end_date={end}",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_revenue_timeline_respects_payment_day(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    owner = await _create_owner(db_session, user)
    renter = await _create_renter(db_session, owner)
    address = await _create_address(db_session, owner)

    today = date.today()
    start = today.replace(day=15)
    end = (today.replace(year=today.year + 1)).replace(day=15)

    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="ACTIVE",
    )

    response = await client.get(
        f"/api/v1/owners/{owner.id}/revenue-timeline?start_date={start}&end_date={end}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    # First payment is next month because payment_day (5) is before start (15).
    first_payment = date.fromisoformat(data[0]["payment_date"])
    assert first_payment.day == 5
    assert first_payment > start


async def test_revenue_timeline_summary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    headers = await _auth_headers(client)
    owner = await _create_owner(db_session, user)
    renter = await _create_renter(db_session, owner)
    address = await _create_address(db_session, owner)

    today = date.today()
    start = today.replace(day=1)
    end = (today.replace(year=today.year + 1)).replace(day=1)
    await _create_contract(
        db_session,
        owner,
        renter,
        address,
        start_date=start,
        end_date=end,
        monthly_revenue=Decimal("1000.00"),
        payment_day=5,
        status="ACTIVE",
    )

    response = await client.get(
        f"/api/v1/owners/{owner.id}/revenue-timeline/summary?start_date={start}&end_date={end}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_amount"] == f"{1000.00 * len(range(0, 12)):.2f}"
    assert data["total_payments"] == 12
