from typing import Any

from fastapi import APIRouter

from app.services.observability.usage_logger import get_analytics_metrics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=dict[str, Any])
def get_analytics() -> dict[str, Any]:
    """Retrieve operational analytics, latency distributions, route splits, and audit logs."""
    return get_analytics_metrics()
