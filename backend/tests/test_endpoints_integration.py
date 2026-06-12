import importlib
import os
import unittest
from contextlib import contextmanager

import httpx
from fastapi import FastAPI

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("PROGRAMADOR_ATUACAO_BASE_URL", "http://programador.local")

auth_router_module = importlib.import_module("app.routers.auth")
configurations_router_module = importlib.import_module("app.routers.configurations")
dependencies_module = importlib.import_module("app.dependencies")
programador_module = importlib.import_module("app.services.programador_atuacao_service")


class StubAuthService:
    def __init__(self) -> None:
        self.authenticate_result = "token-padrao"
        self.authenticate_google_result = {
            "access_token": "google-token",
            "email": "participant@example.com",
            "name": "Participant",
            "is_new_user": False,
        }
        self.create_admin_result = {
            "name": "Administrador",
            "email": "admin@example.com",
            "is_active": True,
        }
        self.generate_reset_code_result = "ABC12345"
        self.reset_password_result = True
        self.change_password_result = True

    async def authenticate(self, email: str, password: str) -> str | None:
        return self.authenticate_result

    async def authenticate_google(self, credential: str) -> dict:
        return dict(self.authenticate_google_result)

    async def create_admin(self, data):
        return self.create_admin_result

    async def generate_reset_code(self, email: str) -> str | None:
        return self.generate_reset_code_result

    async def reset_password(self, email: str, code: str, new_password: str) -> bool:
        return self.reset_password_result

    async def change_password(
        self, email: str, current_password: str, new_password: str
    ) -> bool:
        return self.change_password_result


class StubUserRepository:
    def __init__(self) -> None:
        self.exists_by_email_result = False
        self.created_users: list[dict] = []

    async def exists_by_email(self, email: str) -> bool:
        return self.exists_by_email_result

    async def create(self, data: dict) -> dict:
        self.created_users.append(dict(data))
        return dict(data)


class StubParticipantRepository:
    def __init__(self) -> None:
        self.participant_by_email: dict | None = {
            "id": "part-12345678",
            "name": "Participant",
            "email": "participant@example.com",
            "registered_at": "2026-01-01T10:00:00",
            "consent_accepted": False,
        }
        self.created_participants: list[dict] = []

    async def get_by_email(self, email: str) -> dict | None:
        return self.participant_by_email

    async def create(self, data: dict) -> dict:
        self.created_participants.append(dict(data))
        self.participant_by_email = dict(data)
        return dict(data)

    async def update_fields(self, participant_id: str, data: dict) -> dict:
        self.participant_by_email = {**(self.participant_by_email or {}), **data}
        return dict(self.participant_by_email)


class StubConfigurationService:
    def __init__(self) -> None:
        self.list_response = {
            "items": [
                {
                    "id": "cfg-001",
                    "name": "Configuração A",
                    "description": "Descrição",
                    "is_active": True,
                    "created_at": "2026-01-01T10:00:00",
                    "updated_at": "2026-01-01T10:00:00",
                }
            ],
            "total": 1,
            "message": "Configurations retrieved successfully.",
        }
        self.detail_response = {
            "id": "cfg-001",
            "name": "Configuração A",
            "description": "Descrição",
            "is_active": True,
            "created_at": "2026-01-01T10:00:00",
            "updated_at": "2026-01-01T10:00:00",
            "parameters": {
                "movement_speed": 0.8,
                "movement_duration_seconds": 30,
                "video_capture_enabled": True,
                "audio_capture_enabled": False,
            },
        }
        self.current_response = {
            "configuration": None,
            "source": "none",
            "has_active_configuration": False,
            "message": "No configurations are registered in the system.",
        }
        self.selection_response = {
            "configuration": {
                **self.detail_response,
            },
            "message": "Configuration selected successfully for operation.",
        }
        self.raise_on_activate = None
        self.create_response = dict(self.detail_response)

    def list_configurations(self):
        return self.list_response

    def get_configuration_by_id(self, configuration_id: str):
        if configuration_id == "missing":
            return None
        return self.detail_response

    def create_configuration(self, configuration_data):
        return self.create_response

    def set_active_configuration(self, configuration_id: str):
        if self.raise_on_activate is not None:
            raise self.raise_on_activate
        if configuration_id == "missing":
            return None
        return self.selection_response

    def get_effective_configuration(self):
        return self.current_response


@contextmanager
def override_module_attr(module, attr_name: str, value):
    original = getattr(module, attr_name)
    setattr(module, attr_name, value)
    try:
        yield
    finally:
        setattr(module, attr_name, original)


class EndpointIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(auth_router_module.router)
        self.app.include_router(configurations_router_module.router)
        async def current_user_override() -> str:
            return "admin@example.com"

        self.app.dependency_overrides[dependencies_module.get_current_user] = (
            current_user_override
        )

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, url, **kwargs)

    async def test_auth_login_returns_token(self) -> None:
        auth_service = StubAuthService()

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "POST",
                "/auth/login",
                json={"email": "admin@example.com", "password": "segredo123"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"access_token": "token-padrao", "token_type": "bearer"},
        )

    async def test_auth_login_returns_401_for_invalid_credentials(self) -> None:
        auth_service = StubAuthService()
        auth_service.authenticate_result = None

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "POST",
                "/auth/login",
                json={"email": "admin@example.com", "password": "errada"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Credenciais inválidas.")

    async def test_register_participante_returns_created_payload(self) -> None:
        user_repo = StubUserRepository()
        participant_repo = StubParticipantRepository()
        participant_repo.participant_by_email = None

        with override_module_attr(auth_router_module, "_user_repo", user_repo):
            with override_module_attr(
                auth_router_module, "_participant_repo", participant_repo
            ):
                response = await self.request(
                    "POST",
                    "/auth/register-participante",
                    json={
                        "nome": "Gabriel",
                        "email": "gabriel@example.com",
                        "password": "segredo123",
                    },
                )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["email"], "gabriel@example.com")
        self.assertEqual(body["nome"], "Gabriel")
        self.assertEqual(body["message"], "Cadastro realizado com sucesso!")

    async def test_register_admin_returns_created_response(self) -> None:
        auth_service = StubAuthService()

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "POST",
                "/auth/register",
                json={
                    "name": "Administrador",
                    "email": "admin@example.com",
                    "password": "segredo123",
                    "password_confirmation": "segredo123",
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "admin@example.com")

    async def test_forgot_password_returns_404_when_email_does_not_exist(self) -> None:
        auth_service = StubAuthService()
        auth_service.generate_reset_code_result = None

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "POST",
                "/auth/forgot-password",
                json={"email": "missing@example.com"},
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "E-mail não cadastrado.")

    async def test_reset_password_returns_400_when_code_is_invalid(self) -> None:
        auth_service = StubAuthService()
        auth_service.reset_password_result = False

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "POST",
                "/auth/reset-password",
                json={
                    "email": "user@example.com",
                    "code": "ABC12345",
                    "password": "nova1234",
                    "password_confirmation": "nova1234",
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Código inválido ou expirado.")

    async def test_change_password_returns_success_message(self) -> None:
        auth_service = StubAuthService()

        with override_module_attr(auth_router_module, "_auth_service", auth_service):
            response = await self.request(
                "PUT",
                "/auth/change-password",
                json={
                    "current_password": "antiga123",
                    "new_password": "nova1234",
                    "new_password_confirmation": "nova1234",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Senha alterada com sucesso.")

    async def test_list_configurations_returns_success_payload(self) -> None:
        configuration_service = StubConfigurationService()

        with override_module_attr(
            configurations_router_module, "configuration_service", configuration_service
        ):
            response = await self.request("GET", "/configurations")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["id"], "cfg-001")

    async def test_get_configuration_detail_returns_404_when_missing(self) -> None:
        configuration_service = StubConfigurationService()

        with override_module_attr(
            configurations_router_module, "configuration_service", configuration_service
        ):
            response = await self.request("GET", "/configurations/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Configuration not found.")

    async def test_activate_configuration_maps_integration_error_to_http(self) -> None:
        configuration_service = StubConfigurationService()
        configuration_service.raise_on_activate = (
            programador_module.ProgramadorAtuacaoIntegrationError(
                "Falha na integração", 502
            )
        )

        with override_module_attr(
            configurations_router_module, "configuration_service", configuration_service
        ):
            response = await self.request("PATCH", "/configurations/cfg-001/activate")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "Falha na integração")

    async def test_create_configuration_returns_201(self) -> None:
        configuration_service = StubConfigurationService()

        with override_module_attr(
            configurations_router_module, "configuration_service", configuration_service
        ):
            response = await self.request(
                "POST",
                "/configurations",
                json={
                    "name": "Nova configuração",
                    "description": "Descrição",
                    "parameters": {
                        "movement_speed": 0.8,
                        "movement_duration_seconds": 30,
                        "video_capture_enabled": True,
                        "audio_capture_enabled": False,
                    },
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], "cfg-001")
