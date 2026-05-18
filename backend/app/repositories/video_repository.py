from datetime import datetime
from typing import Any

from app.database import db


class VideoRepository:
    """Persist canonical uploaded video records in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["videos"]

    async def create(self, video_data: dict[str, Any]) -> dict[str, Any]:
        await self._collection.insert_one(video_data)
        return {k: v for k, v in video_data.items() if k != "_id"}

    async def get_by_id(self, video_id: str) -> dict[str, Any] | None:
        video = await self._collection.find_one({"id": video_id}, {"_id": 0})
        return dict(video) if video is not None else None

    async def list_by_ids(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []

        cursor = self._collection.find({"id": {"$in": video_ids}}, {"_id": 0})
        return [dict(video) for video in await cursor.to_list(length=None)]

    async def list_uploaded_between(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find(
            {"uploaded_at": {"$gte": start_at, "$lte": end_at}},
            {"_id": 0},
        )
        return [dict(video) for video in await cursor.to_list(length=None)]

    async def update_file_metadata(
        self,
        video_id: str,
        file_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        await self._collection.update_one(
            {"id": video_id},
            {
                "$set": {
                    "file_id": file_data["file_id"],
                    "filename": file_data["filename"],
                    "content_type": file_data["content_type"],
                    "size_bytes": file_data["size_bytes"],
                }
            },
        )
        return await self.get_by_id(video_id)

    async def upsert_legacy_video(
        self,
        video_id: str,
        video_data: dict[str, Any],
    ) -> None:
        await self._collection.update_one(
            {"id": video_id},
            {"$setOnInsert": video_data},
            upsert=True,
        )
