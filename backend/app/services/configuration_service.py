from datetime import datetime

from app.schemas.configuration import (
    ConfigurationCreateRequest,
    ConfigurationDetail,
    ConfigurationSelectionResponse,
    EffectiveConfigurationResponse,
    ConfigurationListResponse,
    ConfigurationSummary,
)
from app.services.programador_atuacao_service import (
    ProgramadorAtuacaoService,
    ProgramadorAtuacaoIntegrationError,
)


class ConfigurationService:
    """Apply business rules for configuration read operations."""

    def __init__(self, repository, programador_atuacao_service: ProgramadorAtuacaoService) -> None:
        """
        Store the repository and external integration service dependencies.

        Args:
            repository: Repository instance responsible for data access.
            programador_atuacao_service (ProgramadorAtuacaoService): Service responsible
                for communicating with the Programador de Atuação external API.

        Returns:
            None.
        """
        self._repository = repository
        self._programador_atuacao_service = programador_atuacao_service

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

        The configuration is only persisted as active after the Programador de Atuação
        external API confirms receipt with HTTP 200. Any failure interrupts the
        process and leaves the current active configuration unchanged.

        Args:
            configuration_id (str): The identifier of the configuration to activate.

        Returns:
            ConfigurationSelectionResponse | None: The selected configuration or
                None when the identifier is not found.

        Raises:
            ProgramadorAtuacaoIntegrationError: When the external API call fails or
                returns a non-200 status.
        """
        configurations = self._repository.list_all()
        selected_configuration = self._find_configuration_by_id(
            configurations, configuration_id
        )

        if selected_configuration is None:
            return None

        self._programador_atuacao_service.send_configuration(selected_configuration)

        self._persist_active_configuration(configurations, configuration_id)

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

    def _find_configuration_by_id(
        self,
        configurations: list[dict],
        configuration_id: str,
    ) -> dict | None:
        """
        Return the configuration matching the given identifier.

        Args:
            configurations (list[dict]): Existing configuration records.
            configuration_id (str): The identifier to look up.

        Returns:
            dict | None: The matching configuration or None when not found.
        """
        for configuration in configurations:
            if configuration.get("id") == configuration_id:
                return configuration

        return None

    def _persist_active_configuration(
        self,
        configurations: list[dict],
        configuration_id: str,
    ) -> None:
        """
        Mark the target configuration as active and deactivate all others.

        Args:
            configurations (list[dict]): Existing configuration records.
            configuration_id (str): The identifier of the configuration to activate.

        Returns:
            None.
        """
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat()
        updated_configurations: list[dict] = []

        for configuration in configurations:
            updated = dict(configuration)
            should_be_active = updated.get("id") == configuration_id

            if updated.get("is_active", False) != should_be_active:
                updated["is_active"] = should_be_active
                updated["updated_at"] = timestamp

            updated_configurations.append(updated)

        self._repository.replace_all(updated_configurations)

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