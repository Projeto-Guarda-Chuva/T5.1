from __future__ import annotations

import httpx
import pytest

from app.routers import operation_logs as operation_logs_router_module
from app.services.operation_log_service import OperationLogService
from app.services.programador_atuacao_service import (
    ProgramadorAtuacaoIntegrationError,
    ProgramadorAtuacaoService,
)
from tests.support import build_app, request


def _raw_log(
    *,
    configuration_id: str = "cfg-001",
    is_active: bool = True,
    video_capture_enabled: bool = True,
    audio_capture_enabled: bool = False,
) -> dict:
    return {
        "timestamp": "2026-01-01T10:00:00+00:00",
        "payload": {
            "id": configuration_id,
            "name": f"Configuração {configuration_id}",
            "is_active": is_active,
            "parameters": {
                "movement_speed": 0.8,
                "movement_duration_seconds": 30,
                "video_capture_enabled": video_capture_enabled,
                "audio_capture_enabled": audio_capture_enabled,
            },
        },
    }


def test_operation_log_service_returns_empty_message_when_no_logs(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.programador_atuacao_service.ProgramadorAtuacaoService.fetch_logs",
        lambda self: [],
    )

    response = OperationLogService().list_operation_logs()

    assert response.total == 0
    assert response.message == "Nenhum log encontrado."


@pytest.mark.parametrize(
    ("is_active", "video_enabled", "audio_enabled", "status", "status_text"),
    [
        (True, True, False, "success", "Concluído"),
        (True, False, True, "success", "Concluído"),
        (False, True, True, "error", "Inativo ou sem captura"),
        (True, False, False, "error", "Inativo ou sem captura"),
    ],
)
def test_operation_log_service_normalizes_status_from_payload(
    monkeypatch,
    is_active: bool,
    video_enabled: bool,
    audio_enabled: bool,
    status: str,
    status_text: str,
) -> None:
    monkeypatch.setattr(
        "app.services.programador_atuacao_service.ProgramadorAtuacaoService.fetch_logs",
        lambda self: [
            _raw_log(
                is_active=is_active,
                video_capture_enabled=video_enabled,
                audio_capture_enabled=audio_enabled,
            )
        ],
    )

    response = OperationLogService().list_operation_logs()

    assert response.total == 1
    assert response.items[0].status == status
    assert response.items[0].status_text == status_text
    assert "Vídeo" in response.items[0].description


@pytest.mark.asyncio
async def test_operation_logs_route_maps_external_integration_error(monkeypatch) -> None:
    class StubOperationLogService:
        def list_operation_logs(self):
            raise ProgramadorAtuacaoIntegrationError("Falha ao buscar logs", 503)

    monkeypatch.setattr(
        operation_logs_router_module,
        "operation_log_service",
        StubOperationLogService(),
    )
    app = build_app(operation_logs_router_module.router)

    response = await request(app, "GET", "/operation-logs")

    assert response.status_code == 503
    assert response.json()["detail"] == "Falha ao buscar logs"


@pytest.mark.asyncio
async def test_operation_logs_route_returns_normalized_payload(monkeypatch) -> None:
    class StubOperationLogService:
        def list_operation_logs(self):
            return {
                "items": [
                    {
                        "id": "cfg-001",
                        "occurred_at": "2026-01-01T10:00:00+00:00",
                        "duration_seconds": 30,
                        "participant_email": "",
                        "status": "success",
                        "status_text": "Concluído",
                        "description": "Descrição",
                    }
                ],
                "total": 1,
                "message": "Logs recuperados com sucesso.",
            }

    monkeypatch.setattr(
        operation_logs_router_module,
        "operation_log_service",
        StubOperationLogService(),
    )
    app = build_app(operation_logs_router_module.router)

    response = await request(app, "GET", "/operation-logs")

    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "success"


def test_programador_atuacao_service_fetch_logs_maps_request_error(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    def raising_get(*args, **kwargs):
        raise httpx.RequestError("offline")

    monkeypatch.setattr("app.services.programador_atuacao_service.httpx.get", raising_get)

    with pytest.raises(ProgramadorAtuacaoIntegrationError) as exc:
        service.fetch_logs()

    assert exc.value.status_code == 502
    assert "Failed to reach Programador de Atuação" in str(exc.value)


def test_programador_atuacao_service_fetch_logs_rejects_non_200(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    class ResponseStub:
        status_code = 500
        text = "boom"

        @staticmethod
        def json():
            return []

    monkeypatch.setattr(
        "app.services.programador_atuacao_service.httpx.get",
        lambda *args, **kwargs: ResponseStub(),
    )

    with pytest.raises(ProgramadorAtuacaoIntegrationError) as exc:
        service.fetch_logs()

    assert exc.value.status_code == 500
    assert "unexpected status" in str(exc.value)


def test_programador_atuacao_service_fetch_logs_returns_json_payload(monkeypatch) -> None:
    service = ProgramadorAtuacaoService()

    class ResponseStub:
        status_code = 200
        text = "ok"

        @staticmethod
        def json():
            return [{"timestamp": "2026-01-01T10:00:00+00:00"}]

    monkeypatch.setattr(
        "app.services.programador_atuacao_service.httpx.get",
        lambda *args, **kwargs: ResponseStub(),
    )

    assert service.fetch_logs() == [{"timestamp": "2026-01-01T10:00:00+00:00"}]
