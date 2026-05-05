from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.auth_config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.repositories.user_repository import UserRepository

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def authenticate(self, username: str, password: str) -> str | None:
        user = self._repository.get_by_username(username)

        if user is None or not user.get("is_active"):
            return None

        if not _pwd_context.verify(password, user["hashed_password"]):
            return None

        return self._create_access_token({"sub": user["username"]})

    def _create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
