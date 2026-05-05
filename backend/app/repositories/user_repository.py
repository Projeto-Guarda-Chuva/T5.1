import json
from pathlib import Path
from typing import Any


class UserRepository:
    def __init__(self, data_file: Path | None = None) -> None:
        default_file = Path(__file__).resolve().parents[1] / "data" / "users.json"
        self._data_file = data_file or default_file

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        if not self._data_file.exists():
            return None

        with self._data_file.open("r", encoding="utf-8") as file:
            users = json.load(file)

        for user in users:
            if user.get("username") == username:
                return user

        return None
