from app.database import db


class UserRepository:
    def __init__(self) -> None:
        self._collection = db["users"]

    async def get_by_username(self, username: str) -> dict | None:
        return await self._collection.find_one({"username": username}, {"_id": 0})

    async def exists_any(self) -> bool:
        count = await self._collection.count_documents({})
        return count > 0

    async def create(self, user: dict) -> None:
        await self._collection.insert_one(user)
