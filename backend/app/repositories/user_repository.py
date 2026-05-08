from app.database import db


class UserRepository:
    def __init__(self) -> None:
        self._collection = db["users"]

    async def get_by_email(self, email: str) -> dict | None:
        return await self._collection.find_one({"email": email}, {"_id": 0})

    async def exists_by_email(self, email: str) -> bool:
        count = await self._collection.count_documents({"email": email})
        return count > 0

    async def exists_any(self) -> bool:
        count = await self._collection.count_documents({})
        return count > 0

    async def create(self, user: dict) -> dict:
        await self._collection.insert_one(user)
        return {k: v for k, v in user.items() if k != "_id"}
