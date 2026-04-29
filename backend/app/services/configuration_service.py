from app.schemas.configuration import (
    ConfigurationDetail,
    ConfigurationListResponse,
    ConfigurationSummary,
)

class ConfigurationService:
    """Apply business rules for configuration read operations."""

    def __init__(self, repository) -> None:
        """
        Store the repository dependency used by the service.

        Args:
            repository: Repository instance responsible for data access.

        Returns:
            None.
        """
        self._repository = repository

    def list_configurations(self) -> ConfigurationListResponse:
        """
        Return all configurations formatted for the API response model.

        Args:
            None.

        Returns:
            ConfigurationListResponse: The API response containing configuration summaries.
        """
        configurations = self._repository.list_all()
        items = [
            ConfigurationSummary(
                id=configuration["id"],
                name=configuration["name"],
                description=configuration["description"],
                is_active=configuration["is_active"],
                created_at=configuration["created_at"],
                updated_at=configuration["updated_at"],
            )
            for configuration in configurations
        ]

        if not items:
            return ConfigurationListResponse(
                items=[],
                total=0,
                message="No configurations found.",
            )

        return ConfigurationListResponse(
            items=items,
            total=len(items),
            message="Configurations retrieved successfully.",
        )

    def get_configuration_by_id(self, configuration_id: str) -> ConfigurationDetail | None:
        """
        Return a full configuration payload for a specific identifier.

        Args:
            configuration_id (str): The identifier of the configuration to retrieve.

        Returns:
            ConfigurationDetail | None: The configuration detail or None when not found.
        """
        configuration = self._repository.get_by_id(configuration_id)

        if configuration is None:
            return None

        return ConfigurationDetail(**configuration)
