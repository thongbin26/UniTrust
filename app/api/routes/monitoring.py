from fastapi import APIRouter

from app.core.config import settings
from app.monitoring.repository import get_status
from app.monitoring.models import MonitorStatus

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/status", response_model=MonitorStatus)
def monitoring_status() -> MonitorStatus:
    """Read-only monitor observability; disabled RC runtime stays untouched."""
    return get_status(enabled=settings.monitoring_enabled)
