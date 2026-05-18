from datetime import datetime
from typing import Any

from pymongo import UpdateOne

from app.database import db


class ParticipantVideoRepository:
    """Persist many-to-many links between participants and canonical videos."""

    def __init__(self) -> None:
        self._collection = db["participant_videos"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def insert_many(self, videos: list[dict[str, Any]]) -> None:
        if not videos:
            return

        await self._collection.insert_many(videos, ordered=False)

    async def list_by_participant(
        self,
        participant_id: str,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find({"participant_id": participant_id}, {"_id": 0})
        links = [dict(video_link) for video_link in await cursor.to_list(length=None)]
        return sorted(
            links,
            key=lambda video_link: self._parse_sortable_datetime(
                video_link.get("associated_at")
            ),
            reverse=True,
        )

    async def get_by_id_and_participant(
        self,
        participant_id: str,
        video_id: str,
    ) -> dict[str, Any] | None:
        video_link = await self._collection.find_one(
            {
                "participant_id": participant_id,
                "$or": [{"video_id": video_id}, {"id": video_id}],
            },
            {"_id": 0},
        )
        return dict(video_link) if video_link is not None else None

    async def link_participant_to_video(
        self,
        *,
        participant_id: str,
        video_id: str,
        associated_at: datetime,
        association_source: str,
    ) -> None:
        await self._collection.update_one(
            {"participant_id": participant_id, "video_id": video_id},
            {
                "$setOnInsert": {
                    "id": video_id,
                    "participant_id": participant_id,
                    "video_id": video_id,
                    "associated_at": associated_at,
                    "association_source": association_source,
                }
            },
            upsert=True,
        )

    async def link_participants_to_video(
        self,
        *,
        participant_ids: list[str],
        video_id: str,
        associated_at: datetime,
        association_source: str,
    ) -> list[str]:
        unique_participant_ids = sorted(
            {participant_id for participant_id in participant_ids if participant_id}
        )

        if not unique_participant_ids:
            return []

        operations = [
            UpdateOne(
                {"participant_id": participant_id, "video_id": video_id},
                {
                    "$setOnInsert": {
                        "id": video_id,
                        "participant_id": participant_id,
                        "video_id": video_id,
                        "associated_at": associated_at,
                        "association_source": association_source,
                    }
                },
                upsert=True,
            )
            for participant_id in unique_participant_ids
        ]
        await self._collection.bulk_write(operations, ordered=False)
        return unique_participant_ids

    async def migrate_legacy_document(
        self,
        *,
        participant_id: str,
        video_id: str,
        associated_at: datetime,
    ) -> None:
        await self._collection.update_one(
            {"participant_id": participant_id, "id": video_id},
            {
                "$set": {
                    "video_id": video_id,
                    "associated_at": associated_at,
                    "association_source": "legacy_migration",
                }
            },
        )

    def _parse_sortable_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.min

        return datetime.min
