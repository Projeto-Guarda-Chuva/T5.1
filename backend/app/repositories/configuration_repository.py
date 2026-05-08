import json
from pathlib import Path
from typing import Any


class ConfigurationRepository:
    """Read configuration records from the local JSON data source."""

    def __init__(self, data_file: Path | None = None) -> None:
        """
        Initialize the repository with an optional custom data file.

        Args:
            data_file (Path | None): Optional path to the JSON file used as data source.

        Returns:
            None.
        """
        default_file = Path(__file__).resolve().parents[1] / "data" / "configurations.json"
        self._data_file = data_file or default_file

    def list_all(self) -> list[dict[str, Any]]:
        """
        Load and return all configuration records from the JSON file.

        Args:
            None.

        Returns:
            list[dict[str, Any]]: A list of configuration dictionaries.
        """
        if not self._data_file.exists():
            return []

        with self._data_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("The configurations file must contain a list.")

        return data

    def replace_all(self, configurations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Replace all stored configuration records in the JSON file.

        Args:
            configurations (list[dict[str, Any]]): The full set of configuration records.

        Returns:
            list[dict[str, Any]]: The persisted configuration records.
        """
        self._write_all(configurations)
        return configurations

    def get_by_id(self, configuration_id: str) -> dict[str, Any] | None:
        """
        Return a single configuration record by its identifier.

        Args:
            configuration_id (str): The configuration identifier to search for.

        Returns:
            dict[str, Any] | None: The matching configuration or None when not found.
        """
        for configuration in self.list_all():
            if configuration.get("id") == configuration_id:
                return configuration

        return None

    def create(self, configuration_data: dict[str, Any]) -> dict[str, Any]:
        """
        Persist a new configuration record in the JSON file.

        Args:
            configuration_data (dict[str, Any]): The configuration payload to save.

        Returns:
            dict[str, Any]: The saved configuration payload.
        """
        configurations = self.list_all()
        configurations.append(configuration_data)
        self._write_all(configurations)

        return configuration_data

    def _write_all(self, configurations: list[dict[str, Any]]) -> None:
        """
        Persist the provided configuration collection to the JSON file.

        Args:
            configurations (list[dict[str, Any]]): The configuration collection to persist.

        Returns:
            None.
        """
        with self._data_file.open("w", encoding="utf-8") as file:
            json.dump(configurations, file, indent=2, ensure_ascii=False)
            file.write("\n")
