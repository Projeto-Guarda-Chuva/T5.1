from app.database import db


class UserRepository:
    def __init__(self) -> None:
        self._collection = db["users"]
        self._reset_codes = db["password_reset_codes"]

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

    async def update_password(self, email: str, hashed_password: str) -> None:
        await self._collection.update_one(
            {"email": email},
            {"$set": {"hashed_password": hashed_password}},
        )

    async def save_reset_code(self, email: str, code: str, expires_at: str) -> None:
        await self._reset_codes.delete_many({"email": email})
        await self._reset_codes.insert_one({"email": email, "code": code, "expires_at": expires_at})

    async def get_reset_code(self, email: str) -> dict | None:
        return await self._reset_codes.find_one({"email": email}, {"_id": 0})

    async def delete_reset_code(self, email: str) -> None:
        await self._reset_codes.delete_many({"email": email})
