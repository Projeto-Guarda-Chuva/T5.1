from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.auth_config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
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

    def _create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
