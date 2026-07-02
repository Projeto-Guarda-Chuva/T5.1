from __future__ import annotations

from datetime import datetime

import httpx
import pytest
from pydantic import ValidationError

from app.routers import configurations as configurations_router_module
from app.schemas.configuration import ConfigurationCreateRequest
from app.services.configuration_service import ConfigurationService
from app.services.programador_atuacao_service import (
    ProgramadorAtuacaoIntegrationError,
    ProgramadorAtuacaoService,
)
from app.repositories.configuration_repository import ConfigurationRepository
from tests.support import (
    FakeConfigurationRepository,
    FakeProgramadorAtuacaoService,
    build_app,
    request,
)


def _configuration(
    configuration_id: str,
    *,
    is_active: bool = False,
    created_at: str = "2026-01-01T10:00:00",
    updated_at: str = "2026-01-01T10:00:00",
) -> dict:
    return {
        "id": configuration_id,
        "name": f"Configuração {configuration_id}",
        "description": "Descrição",
        "is_active": is_active,
        "created_at": created_at,
        "updated_at": updated_at,
        "parameters": {
            "movement_speed": 0.8,
            "movement_duration_seconds": 30,
            "video_capture_enabled": True,
            "audio_capture_enabled": False,
        },
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "name": "",
                "description": "Descrição",
                "parameters": {
                    "movement_speed": 0.8,
                    "movement_duration_seconds": 30,
                    "video_capture_enabled": True,
                    "audio_capture_enabled": False,
                },
            },
            "at least 1 character",
        ),
        (
            {
                "name": "Configuração",
                "description": "",
                "parameters": {
                    "movement_speed": 0.8,
                    "movement_duration_seconds": 30,
                    "video_capture_enabled": True,
                    "audio_capture_enabled": False,
                },
            },
            "at least 1 character",
        ),
        (
            {
                "name": "Configuração",
                "description": "Descrição",
                "parameters": {
                    "movement_speed": 0,
                    "movement_duration_seconds": 30,
                    "video_capture_enabled": True,
                    "audio_capture_enabled": False,
                },
            },
            "greater than 0",
        ),
        (
            {
                "name": "Configuração",
                "description": "Descrição",
                "parameters": {
                    "movement_speed": 0.8,
                    "movement_duration_seconds": 0,
                    "video_capture_enabled": True,
                    "audio_capture_enabled": False,
                },
            },
            "greater than 0",
        ),
    ],
)
def test_configuration_create_request_rejects_invalid_payload(payload: dict, message: str) -> None:
    with pytest.raises(ValidationError) as exc:
        ConfigurationCreateRequest(**payload)

    assert message in str(exc.value)


def test_configuration_repository_reads_and_persists_records(tmp_path) -> None:
    data_file = tmp_path / "configurations.json"
    repository = ConfigurationRepository(data_file)

    assert repository.list_all() == []

    created = repository.create(_configuration("cfg-001"))
    assert created["id"] == "cfg-001"
    assert repository.get_by_id("cfg-001")["name"] == "Configuração cfg-001"

    repository.replace_all([_configuration("cfg-002", is_active=True)])

    assert repository.list_all()[0]["id"] == "cfg-002"
    assert repository.get_by_id("missing") is None


def test_configuration_repository_rejects_non_list_payload(tmp_path) -> None:
    data_file = tmp_path / "configurations.json"
    data_file.write_text("{}", encoding="utf-8")
    repository = ConfigurationRepository(data_file)

    with pytest.raises(ValueError) as exc:
        repository.list_all()

    assert "must contain a list" in str(exc.value)


def test_list_configurations_returns_empty_message_when_repository_has_no_items() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(),
        FakeProgramadorAtuacaoService(),
    )

    response = service.list_configurations()

    assert response.total == 0
    assert response.message == "No configurations found."


def test_list_configurations_warns_when_none_is_active() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository([_configuration("cfg-001", is_active=False)]),
        FakeProgramadorAtuacaoService(),
    )

    response = service.list_configurations()

    assert response.total == 1
    assert "No active configuration selected" in response.message


def test_list_configurations_returns_success_message_when_an_active_item_exists() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository([_configuration("cfg-001", is_active=True)]),
        FakeProgramadorAtuacaoService(),
    )

    response = service.list_configurations()

    assert response.message == "Configurations retrieved successfully."


def test_get_configuration_by_id_returns_none_for_unknown_identifier() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository([_configuration("cfg-001")]),
        FakeProgramadorAtuacaoService(),
    )

    assert service.get_configuration_by_id("missing") is None


def test_get_configuration_by_id_returns_detail_when_identifier_exists() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository([_configuration("cfg-001")]),
        FakeProgramadorAtuacaoService(),
    )

    assert service.get_configuration_by_id("cfg-001").id == "cfg-001"


def test_set_active_configuration_returns_none_when_identifier_does_not_exist() -> None:
    repository = FakeConfigurationRepository([_configuration("cfg-001")])
    service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

    assert service.set_active_configuration("missing") is None
    assert repository.replaced_with is None


def test_set_active_configuration_persists_single_active_item() -> None:
    repository = FakeConfigurationRepository(
        [
            _configuration("cfg-001", is_active=True),
            _configuration(
                "cfg-002",
                is_active=False,
                created_at="2026-01-02T10:00:00",
                updated_at="2026-01-02T10:00:00",
            ),
        ]
    )
    external_service = FakeProgramadorAtuacaoService()
    service = ConfigurationService(repository, external_service)

    response = service.set_active_configuration("cfg-002")

    assert response.configuration.id == "cfg-002"
    assert external_service.sent_configurations[0]["id"] == "cfg-002"
    assert repository.replaced_with is not None
    active_ids = [item["id"] for item in repository.replaced_with if item["is_active"]]
    assert active_ids == ["cfg-002"]


def test_get_effective_configuration_uses_default_oldest_when_none_is_active() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(
            [
                _configuration(
                    "cfg-002",
                    created_at="2026-01-02T10:00:00",
                    updated_at="2026-01-02T10:00:00",
                ),
                _configuration("cfg-001"),
            ]
        ),
        FakeProgramadorAtuacaoService(),
    )

    response = service.get_effective_configuration()

    assert response.source == "default"
    assert response.configuration.id == "cfg-001"


def test_get_effective_configuration_returns_active_configuration_when_present() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(
            [
                _configuration("cfg-001"),
                _configuration("cfg-002", is_active=True),
            ]
        ),
        FakeProgramadorAtuacaoService(),
    )

    response = service.get_effective_configuration()

    assert response.source == "active"
    assert response.configuration.id == "cfg-002"


def test_get_effective_configuration_returns_none_source_when_repository_is_empty() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(),
        FakeProgramadorAtuacaoService(),
    )

    response = service.get_effective_configuration()

    assert response.source == "none"
    assert response.configuration is None


def test_create_configuration_generates_next_sequential_identifier() -> None:
    repository = FakeConfigurationRepository(
        [
            _configuration("cfg-002"),
            _configuration("legacy"),
        ]
    )
    service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

    created = service.create_configuration(
        ConfigurationCreateRequest(
            name="Nova configuração",
            description="Descrição",
            parameters={
                "movement_speed": 0.8,
                "movement_duration_seconds": 30,
                "video_capture_enabled": True,
                "audio_capture_enabled": False,
            },
        )
    )

    assert created.id == "cfg-003"
    assert repository.created_payload["id"] == "cfg-003"
    assert created.is_active is False


def test_generate_next_id_ignores_non_numeric_cfg_suffixes() -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(),
        FakeProgramadorAtuacaoService(),
    )

    assert service._generate_next_id([{"id": "cfg-abc"}, {"id": "cfg-009"}]) == "cfg-010"


def test_set_active_configuration_keeps_timestamps_when_state_does_not_change() -> None:
    repository = FakeConfigurationRepository([_configuration("cfg-001", is_active=True)])
    service = ConfigurationService(repository, FakeProgramadorAtuacaoService())

    service.set_active_configuration("cfg-001")

    assert repository.replaced_with[0]["updated_at"] == "2026-01-01T10:00:00"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-01-01T10:00:00", datetime(2026, 1, 1, 10, 0, 0)),
        ("", datetime.max),
        ("not-a-date", datetime.max),
        (None, datetime.max),
    ],
)
def test_parse_sortable_datetime_handles_invalid_values(
    value: str | None,
    expected: datetime,
) -> None:
    service = ConfigurationService(
        FakeConfigurationRepository(),
        FakeProgramadorAtuacaoService(),
    )

    assert service._parse_sortable_datetime(value) == expected


@pytest.mark.asyncio
async def test_activate_configuration_route_maps_missing_and_integration_error(monkeypatch) -> None:
    class StubConfigurationService:
        def set_active_configuration(self, configuration_id: str):
            if configuration_id == "missing":
                return None
            raise ProgramadorAtuacaoIntegrationError("Falha na integração", 502)

    monkeypatch.setattr(
        configurations_router_module,
        "configuration_service",
        StubConfigurationService(),
    )
    app = build_app(configurations_router_module.router)

    missing_response = await request(app, "PATCH", "/configurations/missing/activate")
    error_response = await request(app, "PATCH", "/configurations/cfg-001/activate")

    assert missing_response.status_code == 404
    assert missing_response.json()["detail"] == "Configuration not found."
    assert error_response.status_code == 502
    assert error_response.json()["detail"] == "Falha na integração"


@pytest.mark.asyncio
async def test_activate_configuration_route_returns_success_payload(monkeypatch) -> None:
    class StubConfigurationService:
        def set_active_configuration(self, configuration_id: str):
            return {
                "configuration": _configuration(configuration_id, is_active=True),
                "message": "Configuration selected successfully for operation.",
            }

    monkeypatch.setattr(
        configurations_router_module,
        "configuration_service",
        StubConfigurationService(),
    )
    app = build_app(configurations_router_module.router)

    response = await request(app, "PATCH", "/configurations/cfg-001/activate")

    assert response.status_code == 200
    assert response.json()["configuration"]["id"] == "cfg-001"


@pytest.mark.asyncio
async def test_configuration_routes_return_serialized_payloads(monkeypatch) -> None:
    class StubConfigurationService:
        def list_configurations(self):
            return {
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

        def create_configuration(self, configuration_data):
            return _configuration("cfg-001")

        def get_effective_configuration(self):
            return {
                "configuration": _configuration("cfg-001", is_active=True),
                "source": "active",
                "has_active_configuration": True,
                "message": "Active configuration retrieved successfully.",
            }

        def get_configuration_by_id(self, configuration_id: str):
            if configuration_id == "missing":
                return None
            return _configuration("cfg-001")

    monkeypatch.setattr(
        configurations_router_module,
        "configuration_service",
        StubConfigurationService(),
    )
    app = build_app(configurations_router_module.router)

    list_response = await request(app, "GET", "/configurations")
    create_response = await request(
        app,
        "POST",
        "/configurations",
        json={
            "name": "Configuração A",
            "description": "Descrição",
            "parameters": {
                "movement_speed": 0.8,
                "movement_duration_seconds": 30,
                "video_capture_enabled": True,
                "audio_capture_enabled": False,
            },
        },
    )
    current_response = await request(app, "GET", "/configurations/current")
    detail_response = await request(app, "GET", "/configurations/cfg-001")
    missing_response = await request(app, "GET", "/configurations/missing")

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert create_response.status_code == 201
    assert create_response.json()["id"] == "cfg-001"
    assert current_response.json()["source"] == "active"
    assert detail_response.json()["id"] == "cfg-001"
    assert missing_response.status_code == 404


def test_programador_atuacao_service_requires_base_url(monkeypatch) -> None:
    monkeypatch.delenv("PROGRAMADOR_ATUACAO_BASE_URL", raising=False)

    with pytest.raises(RuntimeError) as exc:
        ProgramadorAtuacaoService()

    assert "PROGRAMADOR_ATUACAO_BASE_URL" in str(exc.value)


def test_programador_atuacao_service_send_configuration_maps_request_error(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    def raising_post(*args, **kwargs):
        raise httpx.RequestError("offline")

    monkeypatch.setattr("app.services.programador_atuacao_service.httpx.post", raising_post)

    with pytest.raises(ProgramadorAtuacaoIntegrationError) as exc:
        service.send_configuration({"id": "cfg-001"})

    assert exc.value.status_code == 502
    assert "Failed to reach Programador de Atuação" in str(exc.value)


def test_programador_atuacao_service_send_configuration_rejects_non_200(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    class ResponseStub:
        status_code = 400
        text = "invalid payload"

    monkeypatch.setattr(
        "app.services.programador_atuacao_service.httpx.post",
        lambda *args, **kwargs: ResponseStub(),
    )

    with pytest.raises(ProgramadorAtuacaoIntegrationError) as exc:
        service.send_configuration({"id": "cfg-001"})

    assert exc.value.status_code == 400
    assert "rejected the configuration" in str(exc.value)


def test_programador_atuacao_service_send_configuration_accepts_success_response(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    class ResponseStub:
        status_code = 200
        text = "ok"

    monkeypatch.setattr(
        "app.services.programador_atuacao_service.httpx.post",
        lambda *args, **kwargs: ResponseStub(),
    )

    assert service.send_configuration({"id": "cfg-001"}) is None
