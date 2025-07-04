import logging

from fastapi import APIRouter

from .. import schemas as main_schemas  # Relative import from parent package
from ..api_server import API_VERSION  # Import from main api_server for version

router = APIRouter(
    tags=["Meta"],
)

logger = logging.getLogger(__name__)


@router.get("/health", response_model=main_schemas.HealthCheckResponse)
async def health_check():
    """
    Provides a simple health check endpoint for monitoring.
    """
    # Access API_VERSION from the main api_server module or define it centrally
    return main_schemas.HealthCheckResponse(version=API_VERSION)
