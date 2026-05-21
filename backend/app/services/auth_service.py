import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from jose import jwt
from passlib.context import CryptContext

from app.auth_config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    RESET_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
)
from app.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminCreateRequest, AdminCreateResponse

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class GoogleAuthError(ValueError):
    """Raised when a Google credential is invalid."""


class GoogleAuthConfigurationError(RuntimeError):
    """Raised when Google authentication is not configured."""


class GoogleAuthUnavailableError(RuntimeError):
    """Raised when Google credential validation cannot be completed."""


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

    async def authenticate_google(self, credential: str) -> dict[str, Any]:
        google_profile = await self._verify_google_credential(credential)
        email = str(google_profile.get("email", "")).strip().lower()

        if not email:
            raise GoogleAuthError("A conta do Google não informou um e-mail válido.")

        display_name = str(
            google_profile.get("name")
            or google_profile.get("given_name")
            or email.split("@", 1)[0]
        ).strip()
        google_sub = str(google_profile.get("sub", "")).strip()
        user = await self._repository.get_by_email(email)
        is_new_user = False

        if user is None:
            is_new_user = True
            await self._repository.create(
                {
                    "name": display_name,
                    "nome": display_name,
                    "email": email,
                    "hashed_password": _pwd_context.hash(secrets.token_urlsafe(32)),
                    "is_active": True,
                    "auth_provider": "google",
                    "google_sub": google_sub,
                }
            )
        else:
            if not user.get("is_active"):
                raise GoogleAuthError("Usuário inativo.")

            await self._repository.update_fields(
                email,
                {
                    "name": str(user.get("name") or user.get("nome") or display_name).strip(),
                    "nome": str(user.get("nome") or user.get("name") or display_name).strip(),
                    "auth_provider": "google",
                    "google_sub": google_sub,
                },
            )

        return {
            "access_token": self._create_access_token({"sub": email}),
            "email": email,
            "name": display_name,
            "is_new_user": is_new_user,
        }

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

    async def change_password(
        self, email: str, current_password: str, new_password: str
    ) -> bool:
        user = await self._repository.get_by_email(email)

        if user is None or not _pwd_context.verify(current_password, user["hashed_password"]):
            return False

        hashed = _pwd_context.hash(new_password)
        await self._repository.update_password(email, hashed)
        return True

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

    async def _verify_google_credential(self, credential: str) -> dict[str, Any]:
        normalized_credential = credential.strip()

        if not normalized_credential:
            raise GoogleAuthError("Credential do Google não informado.")

        google_client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
        if not google_client_id:
            raise GoogleAuthConfigurationError(
                "GOOGLE_CLIENT_ID não configurado no backend."
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    settings.GOOGLE_TOKENINFO_URL,
                    params={"id_token": normalized_credential},
                )
        except httpx.HTTPError as exc:
            raise GoogleAuthUnavailableError(
                "Não foi possível validar o login com Google no momento."
            ) from exc

        if response.status_code >= 500:
            raise GoogleAuthUnavailableError(
                "O serviço de validação do Google está indisponível no momento."
            )

        if response.status_code != 200:
            raise GoogleAuthError("Token do Google inválido ou expirado.")

        payload = response.json()
        audience = str(payload.get("aud", "")).strip()

        if audience != google_client_id:
            raise GoogleAuthError("Token do Google emitido para outro cliente.")

        email_verified = str(payload.get("email_verified", "")).strip().lower()
        if email_verified not in {"true", "1"}:
            raise GoogleAuthError("A conta do Google precisa ter e-mail verificado.")

        return payload

    def _create_access_token(self, data: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
