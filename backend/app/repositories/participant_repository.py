from typing import Any

from app.database import db


class ParticipantRepository:
    """Read and persist participant records in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["participants"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def insert_many(self, participants: list[dict[str, Any]]) -> None:
        if not participants:
            return

        await self._collection.insert_many(participants, ordered=False)

    async def get_by_id(self, participant_id: str) -> dict[str, Any] | None:
        participant = await self._collection.find_one({"id": participant_id}, {"_id": 0})

        if participant is None:
            return None

        return dict(participant)
