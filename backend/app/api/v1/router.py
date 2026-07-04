"""API v1 router aggregating all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, owners, renters

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(owners.router)
api_router.include_router(renters.router)
