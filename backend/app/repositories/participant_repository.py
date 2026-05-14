import json
from pathlib import Path
from typing import Any

class ParticipantRepository:
    def __init__(self, data_file: Path | None = None) -> None:
        default_file = Path(__file__).resolve().parents[1] / "data" / "participants.json"
        self._data_file = data_file or default_file

    async def _read_all(self) -> list[dict[str, Any]]:
        if not self._data_file.exists():
            return []
        with self._data_file.open("r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []

    async def _write_all(self, data: list[dict[str, Any]]) -> None:
        with self._data_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        participants = await self._read_all()
        for p in participants:
            if p.get("email") == email:
                return p
        return None

    async def create(self, participant_data: dict[str, Any]) -> dict[str, Any]:
        participants = await self._read_all()
        participants.append(participant_data)
        await self._write_all(participants)
        return participant_data