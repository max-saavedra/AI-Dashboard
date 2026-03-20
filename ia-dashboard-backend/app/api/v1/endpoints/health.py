"""
app/api/v1/endpoints/health.py

GET /api/v1/health

Lightweight health-check endpoint for:
  - GCP Cloud Run liveness and readiness probes
  - CI/CD smoke tests
  - Monitoring dashboards (RNF-10)
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    version: str


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    tags=["ops"],
)
async def health_check() -> HealthStatus:
    """Returns 200 OK with current service status."""
    return HealthStatus(status="ok", version="1.0.0")
