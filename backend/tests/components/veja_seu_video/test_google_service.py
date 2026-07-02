from __future__ import annotations

import httpx
import pytest
from unittest.mock import AsyncMock

from app.services import auth_service as auth_service_module
from app.services.auth_service import (
    AuthService,
    GoogleAuthConfigurationError,
    GoogleAuthError,
    GoogleAuthUnavailableError,
)
from tests.support import FakeUserRepository


class ResponseStub:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return dict(self._payload)


class FakeAsyncClient:
    response: ResponseStub | None = None
    error: Exception | None = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, params: dict) -> ResponseStub:
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


@pytest.mark.asyncio
async def test_authenticate_google_creates_new_user_when_email_is_not_found() -> None:
    repository = FakeUserRepository()
    service = AuthService(repository)
    service._verify_google_credential = AsyncMock(
        return_value={"email": "novo@example.com", "name": "Novo", "sub": "google-123"}
    )

    result = await service.authenticate_google("token")

    assert result["email"] == "novo@example.com"
    assert result["is_new_user"] is True
    assert repository.users["novo@example.com"]["auth_provider"] == "google"


@pytest.mark.asyncio
async def test_authenticate_google_updates_existing_active_user_fields() -> None:
    repository = FakeUserRepository(
        [
            {
                "email": "user@example.com",
                "hashed_password": auth_service_module._pwd_context.hash("segredo123"),
                "is_active": True,
                "name": "",
                "nome": "",
            }
        ]
    )
    service = AuthService(repository)
    service._verify_google_credential = AsyncMock(
        return_value={"email": "user@example.com", "name": "Usuário", "sub": "google-123"}
    )

    result = await service.authenticate_google("token")

    assert result["is_new_user"] is False
    assert repository.updated_fields[-1][1]["google_sub"] == "google-123"
    assert repository.updated_fields[-1][1]["nome"] == "Usuário"


@pytest.mark.asyncio
async def test_authenticate_google_rejects_inactive_or_missing_email_profile() -> None:
    repository = FakeUserRepository(
        [
            {
                "email": "user@example.com",
                "hashed_password": auth_service_module._pwd_context.hash("segredo123"),
                "is_active": False,
                "name": "Usuário",
            }
        ]
    )
    service = AuthService(repository)
    service._verify_google_credential = AsyncMock(
        return_value={"email": "user@example.com", "name": "Usuário", "sub": "google-123"}
    )

    with pytest.raises(GoogleAuthError) as inactive_exc:
        await service.authenticate_google("token")

    assert "Usuário inativo." in str(inactive_exc.value)

    service._verify_google_credential = AsyncMock(return_value={"name": "Sem email"})

    with pytest.raises(GoogleAuthError) as email_exc:
        await service.authenticate_google("token")

    assert "não informou um e-mail válido" in str(email_exc.value)


@pytest.mark.asyncio
async def test_verify_google_credential_rejects_blank_credential() -> None:
    service = AuthService(FakeUserRepository())

    with pytest.raises(GoogleAuthError) as exc:
        await service._verify_google_credential("   ")

    assert "Credential do Google não informado." in str(exc.value)


@pytest.mark.asyncio
async def test_verify_google_credential_requires_google_client_id(monkeypatch) -> None:
    monkeypatch.setattr(auth_service_module.settings, "GOOGLE_CLIENT_ID", None)
    service = AuthService(FakeUserRepository())

    with pytest.raises(GoogleAuthConfigurationError) as exc:
        await service._verify_google_credential("token")

    assert "GOOGLE_CLIENT_ID" in str(exc.value)


@pytest.mark.asyncio
async def test_verify_google_credential_maps_request_and_server_errors(monkeypatch) -> None:
    monkeypatch.setattr(auth_service_module.settings, "GOOGLE_CLIENT_ID", "client-123")
    monkeypatch.setattr(auth_service_module.httpx, "AsyncClient", FakeAsyncClient)
    service = AuthService(FakeUserRepository())

    FakeAsyncClient.error = httpx.RequestError("offline")
    FakeAsyncClient.response = None
    with pytest.raises(GoogleAuthUnavailableError) as request_exc:
        await service._verify_google_credential("token")

    FakeAsyncClient.error = None
    FakeAsyncClient.response = ResponseStub(503, text="down")
    with pytest.raises(GoogleAuthUnavailableError) as server_exc:
        await service._verify_google_credential("token")

    assert "Não foi possível validar" in str(request_exc.value)
    assert "indisponível" in str(server_exc.value)


@pytest.mark.asyncio
async def test_verify_google_credential_rejects_invalid_google_payload(monkeypatch) -> None:
    monkeypatch.setattr(auth_service_module.settings, "GOOGLE_CLIENT_ID", "client-123")
    monkeypatch.setattr(auth_service_module.httpx, "AsyncClient", FakeAsyncClient)
    service = AuthService(FakeUserRepository())

    FakeAsyncClient.error = None
    FakeAsyncClient.response = ResponseStub(401, text="invalid")
    with pytest.raises(GoogleAuthError) as invalid_token_exc:
        await service._verify_google_credential("token")

    FakeAsyncClient.response = ResponseStub(
        200,
        payload={"aud": "other-client", "email_verified": "true", "email": "user@example.com"},
    )
    with pytest.raises(GoogleAuthError) as wrong_audience_exc:
        await service._verify_google_credential("token")

    FakeAsyncClient.response = ResponseStub(
        200,
        payload={"aud": "client-123", "email_verified": "false", "email": "user@example.com"},
    )
    with pytest.raises(GoogleAuthError) as unverified_exc:
        await service._verify_google_credential("token")

    assert "inválido ou expirado" in str(invalid_token_exc.value)
    assert "outro cliente" in str(wrong_audience_exc.value)
    assert "e-mail verificado" in str(unverified_exc.value)


@pytest.mark.asyncio
async def test_verify_google_credential_returns_payload_when_valid(monkeypatch) -> None:
    monkeypatch.setattr(auth_service_module.settings, "GOOGLE_CLIENT_ID", "client-123")
    monkeypatch.setattr(auth_service_module.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.error = None
    FakeAsyncClient.response = ResponseStub(
        200,
        payload={
            "aud": "client-123",
            "email_verified": "true",
            "email": "user@example.com",
            "name": "Usuário",
        },
    )
    service = AuthService(FakeUserRepository())

    payload = await service._verify_google_credential("token")

    assert payload["email"] == "user@example.com"
