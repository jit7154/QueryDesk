from fastapi import APIRouter

from app.config import get_settings
from app.db import check_db_health

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return system health status and database connectivity."""
    settings = get_settings()
    db_ok = check_db_health()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.environment,
        "version": "0.1.0",
    }
