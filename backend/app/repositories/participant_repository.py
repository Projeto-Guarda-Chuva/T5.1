from typing import Any

from app.database import db


class ParticipantRepository:
    """Read and persist participant records in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["participants"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def exists_by_email(self, email: str) -> bool:
        return await self._collection.count_documents({"email": email}) > 0

    async def insert_many(self, participants: list[dict[str, Any]]) -> None:
        if not participants:
            return

        await self._collection.insert_many(participants, ordered=False)

    async def get_by_id(self, participant_id: str) -> dict[str, Any] | None:
        participant = await self._collection.find_one(
            {"id": participant_id},
            {"_id": 0},
        )
        return dict(participant) if participant is not None else None

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        participant = await self._collection.find_one({"email": email}, {"_id": 0})
        return dict(participant) if participant is not None else None

    async def create(self, participant_data: dict[str, Any]) -> dict[str, Any]:
        await self._collection.insert_one(participant_data)
        return {k: v for k, v in participant_data.items() if k != "_id"}

    async def update_fields(
        self,
        participant_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        await self._collection.update_one(
            {"id": participant_id},
            {"$set": updates},
        )
        return await self.get_by_id(participant_id)
