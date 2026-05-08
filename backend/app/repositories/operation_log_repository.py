import json
from pathlib import Path
from typing import Any


class OperationLogRepository:
    """Read operation log records from the local JSON data source."""

    def __init__(self, data_file: Path | None = None) -> None:
        default_file = Path(__file__).resolve().parents[1] / "data" / "operation_logs.json"
        self._data_file = data_file or default_file

    def list_all(self) -> list[dict[str, Any]]:
        """
        Load and return all operation log records from the JSON file.

        Args:
            None.

        Returns:
            list[dict[str, Any]]: A list of operation log dictionaries.
        """
        if not self._data_file.exists():
            return []

        with self._data_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("The operation logs file must contain a list.")

        return data
