from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from gridfs.errors import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.config import settings
from app.database import db


class VideoFileRepository:
    """Persist and retrieve video binary files from MongoDB GridFS."""

    def __init__(self) -> None:
        self._bucket_name = settings.VIDEO_GRIDFS_BUCKET_NAME
        self._bucket = AsyncIOMotorGridFSBucket(db, bucket_name=self._bucket_name)
        self._files_collection = db[f"{self._bucket_name}.files"]

    async def replace_file_for_video(
        self,
        *,
        video_id: str,
        filename: str,
        file_bytes: bytes,
        content_type: str = "video/mp4",
    ) -> dict[str, Any]:
        existing_cursor = self._files_collection.find(
            {
                "$or": [
                    {"metadata.binding_key": f"video:{video_id}"},
                    {"metadata.video_id": video_id},
                ]
            },
            {"_id": 1},
        )
        existing_files = await existing_cursor.to_list(length=None)

        for existing_file in existing_files:
            await self._bucket.delete(existing_file["_id"])

        file_id = await self._bucket.upload_from_stream(
            filename,
            file_bytes,
            metadata={
                "binding_key": f"video:{video_id}",
                "video_id": video_id,
                "content_type": content_type,
            },
        )

        return {
            "file_id": str(file_id),
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes),
        }

    async def get_file(self, file_id: str) -> dict[str, Any] | None:
        try:
            object_id = ObjectId(file_id)
        except InvalidId:
            return None

        try:
            download_stream = await self._bucket.open_download_stream(object_id)
        except NoFile:
            return None

        file_bytes = await download_stream.read()
        metadata = download_stream.metadata or {}

        return {
            "file_id": str(download_stream._id),
            "filename": download_stream.filename,
            "content_type": metadata.get("content_type", "application/octet-stream"),
            "size_bytes": len(file_bytes),
            "content": file_bytes,
            "participant_id": metadata.get("participant_id"),
            "video_id": metadata.get("video_id"),
            "binding_key": metadata.get("binding_key"),
        }

    async def delete_file(self, file_id: str) -> None:
        try:
            object_id = ObjectId(file_id)
        except InvalidId:
            return

        try:
            await self._bucket.delete(object_id)
        except NoFile:
            return
