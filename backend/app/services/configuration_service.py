from datetime import datetime

from app.schemas.configuration import (
    ConfigurationCreateRequest,
    ConfigurationDetail,
    ConfigurationSelectionResponse,
    EffectiveConfigurationResponse,
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
                is_active=configuration.get("is_active", False),
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

        if any(item.is_active for item in items):
            message = "Configurations retrieved successfully."
        else:
            message = (
                "No active configuration selected. The default configuration "
                "will be used during operation."
            )

        return ConfigurationListResponse(
            items=items,
            total=len(items),
            message=message,
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

    def set_active_configuration(
        self,
        configuration_id: str,
    ) -> ConfigurationSelectionResponse | None:
        """
        Select a configuration for use and ensure it is the only active one.

        Args:
            configuration_id (str): The identifier of the configuration to activate.

        Returns:
            ConfigurationSelectionResponse | None: The selected configuration or None when not found.
        """
        configurations = self._repository.list_all()
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat()
        selected_configuration: dict | None = None
        updated_configurations: list[dict] = []

        for configuration in configurations:
            updated_configuration = dict(configuration)
            should_be_active = configuration.get("id") == configuration_id

            if should_be_active:
                selected_configuration = updated_configuration

            if updated_configuration.get("is_active", False) != should_be_active:
                updated_configuration["is_active"] = should_be_active
                updated_configuration["updated_at"] = timestamp

            updated_configurations.append(updated_configuration)

        if selected_configuration is None:
            return None

        self._repository.replace_all(updated_configurations)

        return ConfigurationSelectionResponse(
            configuration=ConfigurationDetail(**selected_configuration),
            message="Configuration selected successfully for operation.",
        )

    def get_effective_configuration(self) -> EffectiveConfigurationResponse:
        """
        Return the configuration effectively used by the operation layer.

        Args:
            None.

        Returns:
            EffectiveConfigurationResponse: The active configuration or the default fallback.
        """
        configurations = self._repository.list_all()

        if not configurations:
            return EffectiveConfigurationResponse(
                configuration=None,
                source="none",
                has_active_configuration=False,
                message="No configurations are registered in the system.",
            )

        active_configuration = self._find_active_configuration(configurations)

        if active_configuration is not None:
            return EffectiveConfigurationResponse(
                configuration=ConfigurationDetail(**active_configuration),
                source="active",
                has_active_configuration=True,
                message="Active configuration retrieved successfully.",
            )

        default_configuration = self._get_default_configuration(configurations)

        return EffectiveConfigurationResponse(
            configuration=ConfigurationDetail(**default_configuration),
            source="default",
            has_active_configuration=False,
            message=(
                "No active configuration is currently selected. "
                "The default configuration is being used."
            ),
        )

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

    def _find_active_configuration(
        self,
        configurations: list[dict],
    ) -> dict | None:
        """
        Return the first configuration marked as active.

        Args:
            configurations (list[dict]): Existing configuration records.

        Returns:
            dict | None: The active configuration or None when there is none.
        """
        for configuration in configurations:
            if configuration.get("is_active", False):
                return configuration

        return None

    def _get_default_configuration(self, configurations: list[dict]) -> dict:
        """
        Return the default configuration used as fallback when none is active.

        The default rule is the oldest registered configuration.

        Args:
            configurations (list[dict]): Existing configuration records.

        Returns:
            dict: The default configuration selected by the fallback rule.
        """
        return min(
            configurations,
            key=lambda configuration: (
                self._parse_sortable_datetime(configuration.get("created_at")),
                configuration.get("id", ""),
            ),
        )

    def _parse_sortable_datetime(self, value: str | None) -> datetime:
        """
        Convert an ISO timestamp to a sortable datetime value.

        Args:
            value (str | None): ISO timestamp string.

        Returns:
            datetime: Parsed datetime or datetime.max when the input is invalid.
        """
        if not value:
            return datetime.max

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.max
