
from fastapi import FastAPI

from business_orchestrator.api.v1.router import api_router
from business_orchestrator.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="AI-powered business orchestration and autonomous workforce platform.",
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
