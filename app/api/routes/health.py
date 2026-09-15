from fastapi import APIRouter

from app.core.config import settings
from app.db.database import database_is_ready


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict:
    database_ready = database_is_ready()

    return {
        "status": "ok" if database_ready else "degraded",
        "service": settings.app_name,
        "environment": settings.app_env,
        "database": "ok" if database_ready else "unavailable",
    }