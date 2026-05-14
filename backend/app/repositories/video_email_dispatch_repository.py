from typing import Any

from app.database import db


class VideoEmailDispatchRepository:
    """Persist video email dispatch audit records in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["video_email_dispatch_logs"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def insert_many(self, dispatches: list[dict[str, Any]]) -> None:
        if not dispatches:
            return

        await self._collection.insert_many(dispatches, ordered=False)

    async def create(self, dispatch_data: dict[str, Any]) -> dict[str, Any]:
        saved_dispatch = dict(dispatch_data)
        saved_dispatch.setdefault("id", await self._generate_next_id())
        await self._collection.insert_one(saved_dispatch)
        return saved_dispatch

    async def _generate_next_id(self) -> str:
        dispatches = await self._collection.find(
            {"id": {"$regex": r"^dispatch-"}},
            {"_id": 0, "id": 1},
        ).to_list(length=None)
        highest_number = 0

        for dispatch in dispatches:
            dispatch_id = dispatch.get("id", "")

            if not dispatch_id.startswith("dispatch-"):
                continue

            suffix = dispatch_id.removeprefix("dispatch-")

            if suffix.isdigit():
                highest_number = max(highest_number, int(suffix))

        return f"dispatch-{highest_number + 1:03d}"
