import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")

from app.schemas.admin import AdminCreateRequest
from app.services.auth_service import AuthService, GoogleAuthError, _pwd_context


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self.reset_codes: dict[str, dict] = {}
        self.updated_passwords: list[tuple[str, str]] = []
        self.updated_fields: list[tuple[str, dict]] = []

    async def get_by_email(self, email: str) -> dict | None:
        return self.users.get(email)

    async def exists_by_email(self, email: str) -> bool:
        return email in self.users

    async def create(self, user: dict) -> dict:
        self.users[user["email"]] = dict(user)
        return dict(user)

    async def update_fields(self, email: str, updates: dict) -> None:
        self.updated_fields.append((email, dict(updates)))
        self.users[email] = {**self.users[email], **updates}

    async def update_password(self, email: str, hashed_password: str) -> None:
        self.updated_passwords.append((email, hashed_password))
        self.users[email]["hashed_password"] = hashed_password

    async def save_reset_code(self, email: str, code: str, expires_at: str) -> None:
        self.reset_codes[email] = {
            "email": email,
            "code": code,
            "expires_at": expires_at,
        }

    async def get_reset_code(self, email: str) -> dict | None:
        return self.reset_codes.get(email)

    async def delete_reset_code(self, email: str) -> None:
        self.reset_codes.pop(email, None)


class AuthServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = FakeUserRepository()
        self.service = AuthService(self.repository)

    async def test_authenticate_returns_token_for_active_user(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("segredo123"),
            "is_active": True,
        }

        token = await self.service.authenticate("user@example.com", "segredo123")

        self.assertIsInstance(token, str)
        self.assertTrue(token)

    async def test_authenticate_returns_none_for_inactive_user(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("segredo123"),
            "is_active": False,
        }

        token = await self.service.authenticate("user@example.com", "segredo123")

        self.assertIsNone(token)

    async def test_generate_reset_code_persists_code_for_active_user(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("segredo123"),
            "is_active": True,
        }

        code = await self.service.generate_reset_code("user@example.com")

        self.assertRegex(code or "", r"^[A-Z0-9]{8}$")
        self.assertEqual(self.repository.reset_codes["user@example.com"]["code"], code)

    async def test_change_password_updates_hash_when_current_password_matches(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("senha-antiga"),
            "is_active": True,
        }

        changed = await self.service.change_password(
            "user@example.com",
            "senha-antiga",
            "nova1234",
        )

        self.assertTrue(changed)
        _, hashed_password = self.repository.updated_passwords[-1]
        self.assertTrue(_pwd_context.verify("nova1234", hashed_password))

    async def test_reset_password_rejects_expired_code_and_deletes_it(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("senha-antiga"),
            "is_active": True,
        }
        self.repository.reset_codes["user@example.com"] = {
            "email": "user@example.com",
            "code": "ABC12345",
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        }

        changed = await self.service.reset_password(
            "user@example.com",
            "ABC12345",
            "nova1234",
        )

        self.assertFalse(changed)
        self.assertNotIn("user@example.com", self.repository.reset_codes)

    async def test_reset_password_updates_password_and_deletes_code(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "hashed_password": _pwd_context.hash("senha-antiga"),
            "is_active": True,
        }
        self.repository.reset_codes["user@example.com"] = {
            "email": "user@example.com",
            "code": "ABC12345",
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        }

        changed = await self.service.reset_password(
            "user@example.com",
            "ABC12345",
            "nova1234",
        )

        self.assertTrue(changed)
        _, hashed_password = self.repository.updated_passwords[-1]
        self.assertTrue(_pwd_context.verify("nova1234", hashed_password))
        self.assertNotIn("user@example.com", self.repository.reset_codes)

    async def test_create_admin_returns_none_when_email_already_exists(self) -> None:
        self.repository.users["admin@example.com"] = {
            "email": "admin@example.com",
            "hashed_password": _pwd_context.hash("segredo123"),
            "is_active": True,
        }

        created = await self.service.create_admin(
            AdminCreateRequest(
                name="Admin",
                email="admin@example.com",
                password="segredo123",
                password_confirmation="segredo123",
            )
        )

        self.assertIsNone(created)

    async def test_authenticate_google_creates_user_when_not_found(self) -> None:
        self.service._verify_google_credential = AsyncMock(
            return_value={
                "email": "novo@example.com",
                "name": "Novo Usuário",
                "sub": "google-123",
            }
        )

        result = await self.service.authenticate_google("credential-valida")

        self.assertEqual(result["email"], "novo@example.com")
        self.assertTrue(result["is_new_user"])
        created_user = self.repository.users["novo@example.com"]
        self.assertEqual(created_user["auth_provider"], "google")
        self.assertEqual(created_user["google_sub"], "google-123")

    async def test_authenticate_google_rejects_inactive_existing_user(self) -> None:
        self.repository.users["user@example.com"] = {
            "email": "user@example.com",
            "nome": "User",
            "hashed_password": _pwd_context.hash("segredo123"),
            "is_active": False,
        }
        self.service._verify_google_credential = AsyncMock(
            return_value={
                "email": "user@example.com",
                "name": "User",
                "sub": "google-123",
            }
        )

        with self.assertRaises(GoogleAuthError) as context:
            await self.service.authenticate_google("credential-valida")

        self.assertIn("Usuário inativo.", str(context.exception))
