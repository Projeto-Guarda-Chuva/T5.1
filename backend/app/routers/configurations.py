from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    ConfigurationCreateRequest,
    ConfigurationDetail,
    ConfigurationSelectionResponse,
    EffectiveConfigurationResponse,
    ConfigurationListResponse,
)
from app.services.configuration_service import ConfigurationService

router = APIRouter(tags=["Configurations"], dependencies=[Depends(get_current_user)])

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


@router.post(
    "/configurations",
    response_model=ConfigurationDetail,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/configuracoes",
    response_model=ConfigurationDetail,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_configuration(
    configuration_data: ConfigurationCreateRequest,
) -> ConfigurationDetail:
    """
    Create a new configuration and persist it in the system.

    Args:
        configuration_data (ConfigurationCreateRequest): The required configuration payload.

    Returns:
        ConfigurationDetail: The saved configuration including generated metadata.
    """
    return configuration_service.create_configuration(configuration_data)


@router.patch(
    "/configurations/{configuration_id}/activate",
    response_model=ConfigurationSelectionResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Configuration not found.",
        }
    },
)
@router.patch(
    "/configuracoes/{configuration_id}/ativar",
    response_model=ConfigurationSelectionResponse,
    include_in_schema=False,
)
async def activate_configuration(
    configuration_id: str,
) -> ConfigurationSelectionResponse:
    """
    Select a stored configuration for operation and keep it as the only active one.

    Args:
        configuration_id (str): The unique identifier of the configuration to activate.

    Returns:
        ConfigurationSelectionResponse: The configuration selected for use and a status message.

    Raises:
        HTTPException: Raised with status code 404 when the configuration is not found.
    """
    selection = configuration_service.set_active_configuration(configuration_id)

    if selection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found.",
        )

    return selection


@router.get(
    "/configurations/current",
    response_model=EffectiveConfigurationResponse,
)
@router.get(
    "/configuracoes/atual",
    response_model=EffectiveConfigurationResponse,
    include_in_schema=False,
)
async def get_current_configuration() -> EffectiveConfigurationResponse:
    """
    Return the configuration currently applied to the operation layer.

    When there is no active configuration, the oldest registered configuration
    is used as the default fallback and the response message indicates that state.

    Args:
        None.

    Returns:
        EffectiveConfigurationResponse: The active or fallback configuration used by the system.
    """
    return configuration_service.get_effective_configuration()


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
