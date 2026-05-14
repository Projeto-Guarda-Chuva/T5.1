from datetime import date, datetime
from typing import Any

from app.database import db


class ParticipantVideoRepository:
    """Read and persist participant video records in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["participant_videos"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def insert_many(self, videos: list[dict[str, Any]]) -> None:
        if not videos:
            return

        await self._collection.insert_many(videos, ordered=False)

    async def list_by_participant_and_date(
        self,
        participant_id: str,
        reference_date: date,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find({"participant_id": participant_id}, {"_id": 0})
        videos = await cursor.to_list(length=None)
        return [
            dict(video)
            for video in videos
            if self._matches_reference_date(video.get("recorded_at"), reference_date)
        ]

    async def get_by_id_and_participant(
        self,
        participant_id: str,
        video_id: str,
    ) -> dict[str, Any] | None:
        video = await self._collection.find_one(
            {"participant_id": participant_id, "id": video_id},
            {"_id": 0},
        )
        return dict(video) if video is not None else None

    async def attach_file_to_video(
        self,
        participant_id: str,
        video_id: str,
        file_data: dict[str, Any],
    ) -> bool:
        update_result = await self._collection.update_one(
            {"participant_id": participant_id, "id": video_id},
            {
                "$set": {
                    "file_id": file_data["file_id"],
                    "filename": file_data["filename"],
                    "content_type": file_data["content_type"],
                    "size_bytes": file_data["size_bytes"],
                }
            },
        )
        return update_result.matched_count > 0

    def _matches_reference_date(
        self,
        recorded_at: Any,
        reference_date: date,
    ) -> bool:
        if isinstance(recorded_at, datetime):
            return recorded_at.date() == reference_date

        if isinstance(recorded_at, str):
            try:
                return datetime.fromisoformat(recorded_at).date() == reference_date
            except ValueError:
                return recorded_at.startswith(reference_date.isoformat())

        return False
