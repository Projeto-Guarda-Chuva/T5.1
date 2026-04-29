from fastapi import APIRouter, HTTPException, status

from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    ConfigurationDetail,
    ConfigurationListResponse,
)
from app.services.configuration_service import ConfigurationService

router = APIRouter(tags=["Configurations"])

configuration_service = ConfigurationService(ConfigurationRepository())

@router.get(
    "/configurations",
    response_model=ConfigurationListResponse,
)
@router.get(
    "/configuracoes",
    response_model=ConfigurationListResponse,
    include_in_schema=False,
)
async def list_configurations() -> ConfigurationListResponse:
    """
    Return all stored configurations available to the application.

    Args:
        None.

    Returns:
        ConfigurationListResponse: A list of configurations, the total count,
        and a message describing the result.
    """
    return configuration_service.list_configurations()

@router.get(
    "/configurations/{configuration_id}",
    response_model=ConfigurationDetail,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Configuration not found.",
        }
    },
)
@router.get(
    "/configuracoes/{configuration_id}",
    response_model=ConfigurationDetail,
    include_in_schema=False,
)
async def get_configuration_detail(configuration_id: str) -> ConfigurationDetail:
    """
    Return the details for a single configuration by its identifier.

    Args:
        configuration_id (str): The unique identifier of the configuration.

    Returns:
        ConfigurationDetail: The full configuration payload when the record exists.

    Raises:
        HTTPException: Raised with status code 404 when the configuration is not found.
    """
    configuration = configuration_service.get_configuration_by_id(configuration_id)

    if configuration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    return configuration
