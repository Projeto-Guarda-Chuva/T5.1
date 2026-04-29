from datetime import datetime

from app.schemas.configuration import (
    ConfigurationCreateRequest,
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

    def create_configuration(
        self,
        configuration_data: ConfigurationCreateRequest,
    ) -> ConfigurationDetail:
        """
        Create and persist a new configuration record.

        Args:
            configuration_data (ConfigurationCreateRequest): Validated payload received by the API.

        Returns:
            ConfigurationDetail: The newly created configuration with generated metadata.
        """
        existing_configurations = self._repository.list_all()
        configuration_id = self._generate_next_id(existing_configurations)
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat()

        new_configuration = {
            "id": configuration_id,
            "name": configuration_data.name,
            "description": configuration_data.description,
            "is_active": False,
            "created_at": timestamp,
            "updated_at": timestamp,
            "parameters": configuration_data.parameters.model_dump(),
        }

        saved_configuration = self._repository.create(new_configuration)
        return ConfigurationDetail(**saved_configuration)

    def _generate_next_id(self, configurations: list[dict]) -> str:
        """
        Generate the next sequential configuration identifier.

        Args:
            configurations (list[dict]): Existing configuration records.

        Returns:
            str: The next identifier in the cfg-XXX format.
        """
        highest_number = 0

        for configuration in configurations:
            configuration_id = configuration.get("id", "")

            if not configuration_id.startswith("cfg-"):
                continue

            suffix = configuration_id.removeprefix("cfg-")

            if suffix.isdigit():
                highest_number = max(highest_number, int(suffix))

        return f"cfg-{highest_number + 1:03d}"
