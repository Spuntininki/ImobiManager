"""API v1 router aggregating all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    addresses,
    auth,
    contracts,
    owner_documents,
    owners,
    renter_documents,
    renters,
    revenue_timeline,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(owners.router)
api_router.include_router(renters.router)
api_router.include_router(renter_documents.router)
api_router.include_router(addresses.router)
api_router.include_router(owner_documents.router)
api_router.include_router(contracts.router)
api_router.include_router(revenue_timeline.router)
