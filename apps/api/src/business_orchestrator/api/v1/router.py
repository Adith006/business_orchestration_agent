from fastapi import APIRouter, Depends

from business_orchestrator.organizations.router import router as organization_router
from business_orchestrator.security.dependencies import get_current_user
from business_orchestrator.security.router import router as auth_router

api_router = APIRouter()

api_router.include_router(organization_router)
api_router.include_router(auth_router)


@api_router.get("/status", tags=["System"])
async def api_status(
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    return {
        "status": "operational",
        "api_version": "v1",
        "authenticated_user": current_user.email,
    }