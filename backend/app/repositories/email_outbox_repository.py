from typing import Any

from app.database import db


class EmailOutboxRepository:
    """Persist locally queued email payloads in MongoDB."""

    def __init__(self) -> None:
        self._collection = db["email_outbox"]

    async def exists_any(self) -> bool:
        return await self._collection.count_documents({}) > 0

    async def insert_many(self, queued_messages: list[dict[str, Any]]) -> None:
        if not queued_messages:
            return

        await self._collection.insert_many(queued_messages, ordered=False)

    async def create(self, email_payload: dict[str, Any]) -> dict[str, Any]:
        queued_email = dict(email_payload)
        queued_email.setdefault("id", await self._generate_next_id())
        await self._collection.insert_one(queued_email)
        return queued_email

    async def _generate_next_id(self) -> str:
        queued_messages = await self._collection.find(
            {"id": {"$regex": r"^outbox-"}},
            {"_id": 0, "id": 1},
        ).to_list(length=None)
        highest_number = 0

        for queued_message in queued_messages:
            message_id = queued_message.get("id", "")

            if not message_id.startswith("outbox-"):
                continue

            suffix = message_id.removeprefix("outbox-")

            if suffix.isdigit():
                highest_number = max(highest_number, int(suffix))

        return f"outbox-{highest_number + 1:03d}"
