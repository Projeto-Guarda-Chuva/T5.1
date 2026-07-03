from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from jose import jwt
from pydantic import ValidationError

from app.auth_config import ALGORITHM, SECRET_KEY
from app.dependencies import get_current_user
from app.routers import auth as auth_router_module
from app.schemas.admin import AdminCreateRequest
from app.schemas.auth import GoogleLoginRequest, LoginRequest, RegisterRequest
from app.schemas.change_password import ChangePasswordRequest
from app.schemas.password_recovery import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import AuthService, GoogleAuthError, _pwd_context
from app.services import email_service, user_service
from app.routers import users as users_router_module
from tests.support import FakeParticipantRepository, FakeUserRepository, build_app, request


FIXED_NOW = datetime(2026, 1, 3, 15, 45, tzinfo=timezone.utc)


def _user(email: str = "user@example.com", *, active: bool = True, password: str = "segredo123") -> dict:
    return {
        "email": email,
        "hashed_password": _pwd_context.hash(password),
        "is_active": active,
        "name": "Usuário",
    }


@pytest.mark.parametrize(
    ("factory", "kwargs", "message"),
    [
        (
            ChangePasswordRequest,
            {
                "current_password": "antiga123",
                "new_password": "nova1234",
                "new_password_confirmation": "outra",
            },
            "As senhas não coincidem.",
        ),
        (
            ResetPasswordRequest,
            {
                "email": "user@example.com",
                "code": "ABC12345",
                "password": "123",
                "password_confirmation": "123",
            },
            "at least 6 characters",
        ),
        (
            ResetPasswordRequest,
            {
                "email": "user@example.com",
                "code": "ABC12345",
                "password": "nova1234",
                "password_confirmation": "outra1234",
            },
            "As senhas não coincidem.",
        ),
        (
            AdminCreateRequest,
            {
                "name": "Admin",
                "email": "admin@example.com",
                "password": "segredo1",
                "password_confirmation": "segredo2",
            },
            "As senhas não coincidem.",
        ),
        (
            LoginRequest,
            {"email": "admin@example.com", "password": ""},
            "at least 1 character",
        ),
        (
            GoogleLoginRequest,
            {"credential": ""},
            "at least 1 character",
        ),
        (
            ForgotPasswordRequest,
            {"email": "email-invalido"},
            "email address",
        ),
    ],
)
def test_auth_related_schemas_reject_invalid_payloads(factory, kwargs: dict, message: str) -> None:
    with pytest.raises(ValidationError) as exc:
        factory(**kwargs)

    assert message.lower() in str(exc.value).lower()


def test_register_request_accepts_valid_payload() -> None:
    payload = RegisterRequest(
        nome="Gabriel",
        email="gabriel@example.com",
        password="segredo123",
    )

    assert payload.email == "gabriel@example.com"


@pytest.mark.asyncio
async def test_authenticate_returns_token_for_active_user() -> None:
    service = AuthService(FakeUserRepository([_user()]))

    token = await service.authenticate("user@example.com", "segredo123")

    assert isinstance(token, str)
    assert token


@pytest.mark.asyncio
async def test_authenticate_returns_none_for_inactive_or_invalid_user() -> None:
    service = AuthService(FakeUserRepository([_user(active=False)]))

    assert await service.authenticate("user@example.com", "segredo123") is None
    assert await service.authenticate("missing@example.com", "segredo123") is None


@pytest.mark.asyncio
async def test_authenticate_returns_none_for_wrong_password() -> None:
    service = AuthService(FakeUserRepository([_user()]))

    assert await service.authenticate("user@example.com", "errada") is None


@pytest.mark.asyncio
async def test_generate_reset_code_persists_code_for_active_user() -> None:
    repository = FakeUserRepository([_user()])
    service = AuthService(repository)

    code = await service.generate_reset_code("user@example.com")

    assert code is not None
    assert repository.reset_codes["user@example.com"]["code"] == code


@pytest.mark.asyncio
async def test_generate_reset_code_returns_none_for_inactive_or_missing_user() -> None:
    service = AuthService(FakeUserRepository([_user(active=False)]))

    assert await service.generate_reset_code("user@example.com") is None
    assert await service.generate_reset_code("missing@example.com") is None


@pytest.mark.asyncio
async def test_change_password_updates_hash_only_when_current_password_matches() -> None:
    repository = FakeUserRepository([_user(password="senha-antiga")])
    service = AuthService(repository)

    changed = await service.change_password(
        "user@example.com",
        "senha-antiga",
        "nova1234",
    )

    assert changed is True
    assert _pwd_context.verify("nova1234", repository.users["user@example.com"]["hashed_password"])
    assert await service.change_password("user@example.com", "errada", "outra123") is False


@pytest.mark.asyncio
async def test_reset_password_rejects_missing_wrong_or_expired_code() -> None:
    repository = FakeUserRepository([_user(password="senha-antiga")])
    repository.reset_codes["user@example.com"] = {
        "email": "user@example.com",
        "code": "ABC12345",
        "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    }
    service = AuthService(repository)

    assert await service.reset_password("missing@example.com", "ABC12345", "nova1234") is False
    assert await service.reset_password("user@example.com", "XXXX", "nova1234") is False
    assert await service.reset_password("user@example.com", "ABC12345", "nova1234") is False
    assert "user@example.com" not in repository.reset_codes


@pytest.mark.asyncio
async def test_reset_password_updates_hash_and_removes_code_when_valid() -> None:
    repository = FakeUserRepository([_user(password="senha-antiga")])
    repository.reset_codes["user@example.com"] = {
        "email": "user@example.com",
        "code": "ABC12345",
        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }
    service = AuthService(repository)

    changed = await service.reset_password("user@example.com", "ABC12345", "nova1234")

    assert changed is True
    assert _pwd_context.verify("nova1234", repository.users["user@example.com"]["hashed_password"])
    assert "user@example.com" not in repository.reset_codes


@pytest.mark.asyncio
async def test_create_admin_returns_none_when_email_already_exists_and_payload_when_new() -> None:
    existing_repository = FakeUserRepository([_user(email="admin@example.com")])
    existing_service = AuthService(existing_repository)

    assert (
        await existing_service.create_admin(
            AdminCreateRequest(
                name="Admin",
                email="admin@example.com",
                password="segredo123",
                password_confirmation="segredo123",
            )
        )
        is None
    )

    new_repository = FakeUserRepository()
    new_service = AuthService(new_repository)
    created = await new_service.create_admin(
        AdminCreateRequest(
            name="Admin",
            email="admin@example.com",
            password="segredo123",
            password_confirmation="segredo123",
        )
    )

    assert created.email == "admin@example.com"
    assert new_repository.created_users[0]["email"] == "admin@example.com"


def test_get_current_user_accepts_valid_token_and_rejects_invalid_one() -> None:
    token = jwt.encode({"sub": "admin@example.com"}, SECRET_KEY, algorithm=ALGORITHM)
    credentials = SimpleNamespace(credentials=token)

    assert get_current_user(credentials) == "admin@example.com"

    with pytest.raises(Exception) as exc:
        get_current_user(SimpleNamespace(credentials="invalido"))

    assert "Token inválido ou expirado." in str(exc.value)


@pytest.mark.asyncio
async def test_send_password_reset_email_builds_and_sends_message(monkeypatch) -> None:
    class FakeMailer:
        def __init__(self) -> None:
            self.message = None

        async def send_message(self, message) -> None:
            self.message = message

    fake_mailer = FakeMailer()
    monkeypatch.setattr(email_service, "_get_mailer", lambda: fake_mailer)

    await email_service.send_password_reset_email("user@example.com", "ABC12345")

    assert fake_mailer.message.subject == "Recuperação de senha — T5.1"
    assert "ABC12345" in fake_mailer.message.body


def test_get_mailer_uses_expected_gmail_defaults(monkeypatch) -> None:
    monkeypatch.setenv("MAIL_USERNAME", "user")
    monkeypatch.setenv("MAIL_PASSWORD", "pass")
    monkeypatch.setenv("MAIL_FROM", "from@example.com")

    mailer = email_service._get_mailer()

    assert mailer.config.MAIL_SERVER == "smtp.gmail.com"
    assert mailer.config.MAIL_PORT == 587


@pytest.mark.asyncio
async def test_auth_routes_cover_success_error_and_validation_paths(monkeypatch) -> None:
    class StubAuthService:
        def __init__(self) -> None:
            self.authenticate_result = "token-padrao"
            self.create_admin_result = {
                "name": "Administrador",
                "email": "admin@example.com",
                "is_active": True,
            }
            self.generate_reset_code_result = "ABC12345"
            self.reset_password_result = True
            self.change_password_result = True

        async def authenticate(self, email: str, password: str):
            return self.authenticate_result

        async def create_admin(self, data):
            return self.create_admin_result

        async def generate_reset_code(self, email: str):
            return self.generate_reset_code_result

        async def reset_password(self, email: str, code: str, new_password: str):
            return self.reset_password_result

        async def change_password(self, email: str, current_password: str, new_password: str):
            return self.change_password_result

    auth_service = StubAuthService()
    user_repository = FakeUserRepository()
    participant_repository = FakeParticipantRepository()
    participant_repository.by_email["existing@example.com"] = {
        "id": "part-existing",
        "name": "Existente",
        "email": "existing@example.com",
    }
    sent_emails: list[tuple[str, str]] = []

    async def fake_send_password_reset_email(email: str, code: str) -> None:
        sent_emails.append((email, code))

    monkeypatch.setattr(auth_router_module, "_auth_service", auth_service)
    monkeypatch.setattr(auth_router_module, "_user_repo", user_repository)
    monkeypatch.setattr(auth_router_module, "_participant_repo", participant_repository)
    monkeypatch.setattr(auth_router_module, "send_password_reset_email", fake_send_password_reset_email)
    app = build_app(auth_router_module.router, current_user="admin@example.com")

    login_response = await request(
        app,
        "POST",
        "/auth/login",
        json={"email": "admin@example.com", "password": "segredo123"},
    )
    auth_service.authenticate_result = None
    login_error_response = await request(
        app,
        "POST",
        "/auth/login",
        json={"email": "admin@example.com", "password": "errada"},
    )

    register_invalid_response = await request(
        app,
        "POST",
        "/auth/register-participante",
        json={"nome": "", "email": "invalido", "password": ""},
    )
    register_response = await request(
        app,
        "POST",
        "/auth/register-participante",
        json={"nome": "Gabriel", "email": "gabriel@example.com", "password": "segredo123"},
    )
    user_repository.users["dup@example.com"] = _user(email="dup@example.com")
    duplicate_response = await request(
        app,
        "POST",
        "/auth/register-participante",
        json={"nome": "Duplicado", "email": "dup@example.com", "password": "segredo123"},
    )
    existing_participant_response = await request(
        app,
        "POST",
        "/auth/register-participante",
        json={"nome": "Existente", "email": "existing@example.com", "password": "segredo123"},
    )

    admin_response = await request(
        app,
        "POST",
        "/auth/register",
        json={
            "name": "Administrador",
            "email": "admin@example.com",
            "password": "segredo123",
            "password_confirmation": "segredo123",
        },
    )
    auth_service.create_admin_result = None
    admin_conflict_response = await request(
        app,
        "POST",
        "/auth/register",
        json={
            "name": "Administrador",
            "email": "admin@example.com",
            "password": "segredo123",
            "password_confirmation": "segredo123",
        },
    )

    forgot_response = await request(
        app,
        "POST",
        "/auth/forgot-password",
        json={"email": "user@example.com"},
    )
    auth_service.generate_reset_code_result = None
    forgot_missing_response = await request(
        app,
        "POST",
        "/auth/forgot-password",
        json={"email": "missing@example.com"},
    )

    reset_response = await request(
        app,
        "POST",
        "/auth/reset-password",
        json={
            "email": "user@example.com",
            "code": "ABC12345",
            "password": "nova1234",
            "password_confirmation": "nova1234",
        },
    )
    auth_service.reset_password_result = False
    reset_error_response = await request(
        app,
        "POST",
        "/auth/reset-password",
        json={
            "email": "user@example.com",
            "code": "ABC12345",
            "password": "nova1234",
            "password_confirmation": "nova1234",
        },
    )

    change_response = await request(
        app,
        "PUT",
        "/auth/change-password",
        json={
            "current_password": "antiga123",
            "new_password": "nova1234",
            "new_password_confirmation": "nova1234",
        },
    )
    auth_service.change_password_result = False
    change_error_response = await request(
        app,
        "PUT",
        "/auth/change-password",
        json={
            "current_password": "antiga123",
            "new_password": "nova1234",
            "new_password_confirmation": "nova1234",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["access_token"] == "token-padrao"
    assert login_error_response.status_code == 401
    assert register_invalid_response.status_code == 422
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "gabriel@example.com"
    assert duplicate_response.status_code == 409
    assert existing_participant_response.status_code == 201
    assert participant_repository.created[0]["email"] == "gabriel@example.com"
    assert admin_response.status_code == 201
    assert admin_conflict_response.status_code == 409
    assert forgot_response.status_code == 200
    assert sent_emails == [("user@example.com", "ABC12345")]
    assert forgot_missing_response.status_code == 404
    assert reset_response.status_code == 200
    assert reset_error_response.status_code == 400
    assert change_response.status_code == 200
    assert change_error_response.status_code == 400


@pytest.mark.asyncio
async def test_google_auth_route_maps_service_errors(monkeypatch) -> None:
    from app.services.auth_service import (
        GoogleAuthConfigurationError,
        GoogleAuthUnavailableError,
    )

    class StubAuthService:
        def __init__(self, error: Exception) -> None:
            self.error = error

        async def authenticate_google(self, credential: str):
            raise self.error

    errors = [
        (GoogleAuthConfigurationError("config"), 503),
        (GoogleAuthUnavailableError("unavailable"), 502),
        (GoogleAuthError("invalid"), 401),
    ]

    for error, status_code in errors:
        monkeypatch.setattr(auth_router_module, "_auth_service", StubAuthService(error))
        monkeypatch.setattr(auth_router_module, "_participant_repo", FakeParticipantRepository())
        app = build_app(auth_router_module.router)
        response = await request(
            app,
            "POST",
            "/auth/google",
            json={"credential": "token"},
        )
        assert response.status_code == status_code


@pytest.mark.asyncio
async def test_google_auth_route_creates_or_updates_participant_profile(monkeypatch) -> None:
    class StubAuthService:
        async def authenticate_google(self, credential: str):
            return {
                "access_token": "google-token",
                "email": "participant@example.com",
                "name": "Participante",
                "is_new_user": True,
            }

    participant_repository = FakeParticipantRepository()
    monkeypatch.setattr(auth_router_module, "_auth_service", StubAuthService())
    monkeypatch.setattr(auth_router_module, "_participant_repo", participant_repository)
    app = build_app(auth_router_module.router)

    created_response = await request(
        app,
        "POST",
        "/auth/google",
        json={"credential": "token"},
    )

    missing_name_repository = FakeParticipantRepository(
        [
            {
                "id": "part-001",
                "name": "",
                "email": "participant@example.com",
            }
        ]
    )
    monkeypatch.setattr(auth_router_module, "_participant_repo", missing_name_repository)
    updated_response = await request(
        app,
        "POST",
        "/auth/google",
        json={"credential": "token"},
    )

    existing_name_repository = FakeParticipantRepository(
        [
            {
                "id": "part-002",
                "name": "Nome já preenchido",
                "email": "participant@example.com",
            }
        ]
    )
    monkeypatch.setattr(auth_router_module, "_participant_repo", existing_name_repository)
    existing_response = await request(
        app,
        "POST",
        "/auth/google",
        json={"credential": "token"},
    )

    assert created_response.status_code == 200
    assert created_response.json()["participant_id"].startswith("part-")
    assert updated_response.status_code == 200
    assert missing_name_repository.by_id["part-001"]["name"] == "Participante"
    assert existing_response.status_code == 200
    assert existing_name_repository.by_id["part-002"]["name"] == "Nome já preenchido"


def test_legacy_user_service_register_and_login(monkeypatch) -> None:
    users: dict[str, dict] = {}

    monkeypatch.setattr(
        user_service.participant_repository,
        "get_user_by_email",
        lambda email: users.get(email),
        raising=False,
    )
    monkeypatch.setattr(
        user_service.participant_repository,
        "create_user",
        lambda user: users.setdefault(user["email"], dict(user)),
        raising=False,
    )

    created = user_service.register_user(
        SimpleNamespace(
            name="Usuário",
            email="user@example.com",
            password="segredo123",
            consent_accepted=True,
        )
    )

    assert created.user.email == "user@example.com"
    assert created.access_token.startswith("fake-jwt-token-")

    logged_in = user_service.login_user(
        SimpleNamespace(email="user@example.com", password="segredo123")
    )

    assert logged_in.user.email == "user@example.com"

    with pytest.raises(Exception) as duplicate_exc:
        user_service.register_user(
            SimpleNamespace(
                name="Usuário",
                email="user@example.com",
                password="segredo123",
                consent_accepted=True,
            )
        )

    with pytest.raises(Exception) as login_exc:
        user_service.login_user(
            SimpleNamespace(email="user@example.com", password="errada")
        )

    assert "já está em uso" in str(duplicate_exc.value)
    assert "E-mail ou senha incorretos." in str(login_exc.value)


def test_legacy_users_router_uses_user_service(monkeypatch) -> None:
    monkeypatch.setattr(
        users_router_module.user_service,
        "register_user",
        lambda user_data: {
            "access_token": "token-register",
            "user": {"id": "usr-001", "name": "Usuário", "email": "user@example.com"},
        },
    )
    monkeypatch.setattr(
        users_router_module.user_service,
        "login_user",
        lambda user_data: {
            "access_token": "token-login",
            "user": {"id": "usr-001", "name": "Usuário", "email": "user@example.com"},
        },
    )
    register_response = users_router_module.register(
        SimpleNamespace(
            name="Usuário",
            email="user@example.com",
            password="segredo123",
            consent_accepted=True,
        )
    )
    login_response = users_router_module.login(
        SimpleNamespace(email="user@example.com", password="segredo123")
    )

    assert register_response["access_token"] == "token-register"
    assert login_response["access_token"] == "token-login"


@pytest.mark.parametrize(
    "payload",
    [
        {
            "nome": "   ",
            "email": "whitespace-name@example.com",
            "password": "segredo123",
        },
        {
            "nome": "Participante",
            "email": "whitespace-password@example.com",
            "password": "   ",
        },
    ],
)
@pytest.mark.asyncio
async def test_public_registration_route_should_reject_whitespace_only_name_or_password(
    monkeypatch,
    payload: dict,
    case_log,
) -> None:
    case_log["input"] = {
        "route": "/auth/register-participante",
        "payload": payload,
    }
    case_log["notes"] = [
        "Contrato esperado: cadastro público não deve aceitar nome ou senha compostos apenas por espaços.",
    ]

    monkeypatch.setattr(auth_router_module, "_user_repo", FakeUserRepository())
    monkeypatch.setattr(auth_router_module, "_participant_repo", FakeParticipantRepository())
    app = build_app(auth_router_module.router)

    response = await request(
        app,
        "POST",
        "/auth/register-participante",
        json=payload,
    )

    case_log["output"] = {
        "status_code": response.status_code,
        "body": response.text,
    }

    assert response.status_code in {400, 422}
