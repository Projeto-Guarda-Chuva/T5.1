import secrets
import string
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.auth_config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    RESET_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminCreateRequest, AdminCreateResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def authenticate(self, email: str, password: str) -> str | None:
        user = await self._repository.get_by_email(email)

        if user is None or not user.get("is_active"):
            return None

        if not _pwd_context.verify(password, user["hashed_password"]):
            return None

        return self._create_access_token({"sub": user["email"]})

    async def create_admin(self, data: AdminCreateRequest) -> AdminCreateResponse | None:
        if await self._repository.exists_by_email(data.email):
            return None

        new_admin = {
            "name": data.name,
            "email": data.email,
            "hashed_password": _pwd_context.hash(data.password),
            "is_active": True,
        }

        saved = await self._repository.create(new_admin)
        return AdminCreateResponse(
            name=saved["name"],
            email=saved["email"],
            is_active=saved["is_active"],
        )

    async def generate_reset_code(self, email: str) -> str | None:
        user = await self._repository.get_by_email(email)

        if user is None or not user.get("is_active"):
            return None

        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        ).isoformat()

        await self._repository.save_reset_code(email, code, expires_at)
        return code

    async def reset_password(self, email: str, code: str, new_password: str) -> bool:
        record = await self._repository.get_reset_code(email)

        if record is None or record["code"] != code:
            return False

        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            await self._repository.delete_reset_code(email)
            return False

        hashed = _pwd_context.hash(new_password)
        await self._repository.update_password(email, hashed)
        await self._repository.delete_reset_code(email)
        return True

    def _create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
