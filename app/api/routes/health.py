from fastapi import APIRouter, Request

from app.core.config import settings
from app.db.database import database_is_ready


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check(request: Request) -> dict:
    database_ready = database_is_ready()
    components_ready = getattr(request.app.state, "startup_ready", False)

    return {
        "status": "ok" if database_ready and components_ready else "degraded",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database": "ok" if database_ready else "unavailable",
    }
