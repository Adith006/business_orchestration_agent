from fastapi import APIRouter

from business_orchestrator.organizations.router import router as organization_router
from business_orchestrator.security.router import router as auth_router

api_router = APIRouter()

api_router.include_router(organization_router)
api_router.include_router(auth_router)


@api_router.get("/status", tags=["System"])
async def api_status() -> dict[str, str]:
    return {"status": "operational", "api_version": "v1"}