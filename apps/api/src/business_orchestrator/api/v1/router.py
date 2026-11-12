
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/status", tags=["System"])
async def api_status() -> dict[str, str]:
    return {
        "status": "operational",
        "api_version": "v1",
    }
