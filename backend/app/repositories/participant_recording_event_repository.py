from typing import Any

from app.database import db


class ParticipantRecordingEventRepository:
    """Store and query participant recording-intent events."""

    def __init__(self) -> None:
        self._collection = db["participant_recording_events"]

    async def create(self, event_data: dict[str, Any]) -> dict[str, Any]:
        await self._collection.insert_one(event_data)
        return {k: v for k, v in event_data.items() if k != "_id"}

    async def list_distinct_participant_ids_between(
        self,
        *,
        event_type: str,
        start_at,
        end_at,
    ) -> list[str]:
        participant_ids = await self._collection.distinct(
            "participant_id",
            {
                "event_type": event_type,
                "created_at": {"$gte": start_at, "$lte": end_at},
            },
        )
        return [str(participant_id) for participant_id in participant_ids if participant_id]
