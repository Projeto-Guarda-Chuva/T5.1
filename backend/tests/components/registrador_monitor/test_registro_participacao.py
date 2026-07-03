from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.routers import participantes as participantes_router_module
from app.schemas.participant_recording import ParticipationEventResponse
from app.services.participant_recording_service import ParticipantRecordingService
from app.time_utils import normalize_utc_datetime, utc_isoformat
from tests.support import (
    FakeEventRepository,
    FakeParticipantRepository,
    FakeParticipantVideoRepository,
    FakeVideoRepository,
    build_app,
    request,
)


FIXED_NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _participant(
    participant_id: str = "part-001",
    *,
    email: str = "participant@example.com",
) -> dict:
    return {
        "id": participant_id,
        "name": "Participante",
        "email": email,
        "consent_accepted": False,
    }


def _video(
    video_id: str,
    *,
    status: str = "available",
    uploaded_at: datetime = FIXED_NOW,
) -> dict:
    return {
        "id": video_id,
        "title": f"Vídeo {video_id}",
        "status": status,
        "uploaded_at": uploaded_at,
        "recorded_at": uploaded_at,
        "duration_seconds": 0,
        "thumbnail_url": "",
    }


@pytest.mark.asyncio
async def test_mark_will_participate_records_event_and_updates_status(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    event_repository = FakeEventRepository()
    service = ParticipantRecordingService(
        participant_repository=participant_repository,
        event_repository=event_repository,
        video_repository=FakeVideoRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
    )
    monkeypatch.setattr(
        "app.services.participant_recording_service.utc_now",
        lambda: FIXED_NOW,
    )

    response = await service.mark_will_participate("part-001")

    assert response.event_type == "will_participate"
    assert response.recorded_at == FIXED_NOW
    assert response.associated_video_ids == []
    assert event_repository.created_events[0]["event_type"] == "will_participate"
    assert participant_repository.by_id["part-001"]["status_gravacao"] == "ainda_participarei"


@pytest.mark.asyncio
async def test_mark_already_participated_links_only_available_recent_videos(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    event_repository = FakeEventRepository()
    video_repository = FakeVideoRepository(
        [
            _video("vid-001", status="available"),
            _video("vid-002", status="processing"),
            _video("vid-003", status="available"),
        ]
    )
    video_repository.uploaded_between_result = [
        _video("vid-001", status="available"),
        _video("vid-002", status="processing"),
        _video("vid-003", status="available"),
    ]
    participant_video_repository = FakeParticipantVideoRepository()
    service = ParticipantRecordingService(
        participant_repository=participant_repository,
        event_repository=event_repository,
        video_repository=video_repository,
        participant_video_repository=participant_video_repository,
    )
    monkeypatch.setattr(
        "app.services.participant_recording_service.utc_now",
        lambda: FIXED_NOW,
    )

    response = await service.mark_already_participated("part-001")

    assert response.event_type == "already_participated"
    assert response.associated_video_ids == ["vid-001", "vid-003"]
    assert response.associated_videos_count == 2
    assert len(participant_video_repository.linked_single_calls) == 2
    assert participant_repository.by_id["part-001"]["status_gravacao"] == "ja_participei"


@pytest.mark.asyncio
async def test_mark_already_participated_reports_when_no_available_videos(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    video_repository = FakeVideoRepository([_video("vid-001", status="processing")])
    video_repository.uploaded_between_result = [_video("vid-001", status="processing")]
    service = ParticipantRecordingService(
        participant_repository=participant_repository,
        event_repository=FakeEventRepository(),
        video_repository=video_repository,
        participant_video_repository=FakeParticipantVideoRepository(),
    )
    monkeypatch.setattr(
        "app.services.participant_recording_service.utc_now",
        lambda: FIXED_NOW,
    )

    response = await service.mark_already_participated("part-001")

    assert response.associated_video_ids == []
    assert "Nenhum vídeo enviado na última hora" in response.message


@pytest.mark.asyncio
async def test_register_status_rejects_invalid_value() -> None:
    service = ParticipantRecordingService(
        participant_repository=FakeParticipantRepository([_participant()]),
        event_repository=FakeEventRepository(),
        video_repository=FakeVideoRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
    )

    with pytest.raises(ValueError) as exc:
        await service.register_status("part-001", "invalido")

    assert str(exc.value) == "Status inválido."


@pytest.mark.asyncio
async def test_mark_participation_requires_existing_participant() -> None:
    service = ParticipantRecordingService(
        participant_repository=FakeParticipantRepository(),
        event_repository=FakeEventRepository(),
        video_repository=FakeVideoRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
    )

    with pytest.raises(ValueError) as exc:
        await service.mark_will_participate("missing")

    assert str(exc.value) == "Participante não encontrado."


@pytest.mark.asyncio
async def test_register_status_dispatches_to_supported_branches(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    service = ParticipantRecordingService(
        participant_repository=participant_repository,
        event_repository=FakeEventRepository(),
        video_repository=FakeVideoRepository([_video("vid-001")]),
        participant_video_repository=FakeParticipantVideoRepository(),
    )
    monkeypatch.setattr(
        "app.services.participant_recording_service.utc_now",
        lambda: FIXED_NOW,
    )

    will_response = await service.register_status("part-001", "ainda_participarei")
    already_response = await service.register_status("part-001", "ja_participei")

    assert will_response.event_type == "will_participate"
    assert already_response.event_type == "already_participated"


@pytest.mark.asyncio
async def test_current_participant_status_routes_require_existing_participant(monkeypatch, case_log) -> None:
    case_log["input"] = {
        "current_user_email": "missing@example.com",
        "route": "/participantes/me/ainda-vou-participar",
    }

    class StubParticipantRecordingService:
        async def mark_will_participate(self, participant_id: str):
            return {
                "participant_id": participant_id,
                "participant_email": "participant@example.com",
                "event_type": "will_participate",
                "recorded_at": FIXED_NOW,
                "associated_video_ids": [],
                "associated_videos_count": 0,
                "message": "ok",
            }

    monkeypatch.setattr(
        participantes_router_module,
        "participant_recording_service",
        StubParticipantRecordingService(),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository(),
    )
    app = build_app(
        participantes_router_module.router,
        participantes_router_module.router_alias,
        current_user="missing@example.com",
    )

    response = await request(app, "POST", "/participantes/me/ainda-vou-participar")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participante não encontrado."


@pytest.mark.asyncio
async def test_current_participant_status_routes_forward_success_payload(monkeypatch, case_log) -> None:
    case_log["input"] = {
        "current_user_email": "participant@example.com",
        "route": "/participantes/me/ja-participei",
        "expected_event_type": "already_participated",
    }

    class StubParticipantRecordingService:
        async def mark_already_participated(self, participant_id: str):
            return {
                "participant_id": participant_id,
                "participant_email": "participant@example.com",
                "event_type": "already_participated",
                "recorded_at": FIXED_NOW,
                "associated_video_ids": ["vid-001"],
                "associated_videos_count": 1,
                "message": "ok",
            }

    monkeypatch.setattr(
        participantes_router_module,
        "participant_recording_service",
        StubParticipantRecordingService(),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    app = build_app(
        participantes_router_module.router,
        participantes_router_module.router_alias,
        current_user="participant@example.com",
    )

    response = await request(app, "POST", "/participantes/me/ja-participei")

    assert response.status_code == 200
    assert response.json()["event_type"] == "already_participated"
    assert response.json()["associated_video_ids"] == ["vid-001"]


@pytest.mark.asyncio
async def test_current_participant_will_participate_route_returns_success_payload(monkeypatch) -> None:
    class StubParticipantRecordingService:
        async def mark_will_participate(self, participant_id: str):
            return {
                "participant_id": participant_id,
                "participant_email": "participant@example.com",
                "event_type": "will_participate",
                "recorded_at": FIXED_NOW,
                "associated_video_ids": [],
                "associated_videos_count": 0,
                "message": "ok",
            }

    monkeypatch.setattr(
        participantes_router_module,
        "participant_recording_service",
        StubParticipantRecordingService(),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    app = build_app(
        participantes_router_module.router,
        participantes_router_module.router_alias,
        current_user="participant@example.com",
    )

    response = await request(app, "POST", "/participantes/me/ainda-vou-participar")

    assert response.status_code == 200
    assert response.json()["event_type"] == "will_participate"


@pytest.mark.asyncio
async def test_current_participant_already_participated_route_returns_missing_error(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository(),
    )
    app = build_app(
        participantes_router_module.router,
        participantes_router_module.router_alias,
        current_user="missing@example.com",
    )

    response = await request(app, "POST", "/participantes/me/ja-participei")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_status_route_maps_invalid_and_missing_participant(monkeypatch) -> None:
    class StubParticipantRecordingService:
        async def register_status(self, participant_id: str, status_gravacao: str):
            if participant_id == "missing":
                raise ValueError("Participante não encontrado.")
            raise ValueError("Status inválido.")

    monkeypatch.setattr(
        participantes_router_module,
        "participant_recording_service",
        StubParticipantRecordingService(),
    )
    app = build_app(participantes_router_module.router)

    missing_response = await request(
        app,
        "PATCH",
        "/participantes/missing/status",
        json={"status_gravacao": "ja_participei"},
    )
    invalid_response = await request(
        app,
        "PATCH",
        "/participantes/part-001/status",
        json={"status_gravacao": "invalido"},
    )

    assert missing_response.status_code == 404
    assert invalid_response.status_code == 400


@pytest.mark.asyncio
async def test_update_status_route_returns_success_payload(monkeypatch, case_log) -> None:
    case_log["input"] = {
        "route": "/participantes/part-001/status",
        "payload": {"status_gravacao": "ja_participei"},
        "service_return_shape": "ParticipationEventResponse",
    }

    class StubParticipantRecordingService:
        async def register_status(self, participant_id: str, status_gravacao: str):
            return ParticipationEventResponse(
                participant_id=participant_id,
                participant_email="participant@example.com",
                event_type="already_participated",
                recorded_at=FIXED_NOW,
                associated_video_ids=["vid-001"],
                associated_videos_count=1,
                message="ok",
            )

    monkeypatch.setattr(
        participantes_router_module,
        "participant_recording_service",
        StubParticipantRecordingService(),
    )
    app = build_app(participantes_router_module.router)

    try:
        response = await request(
            app,
            "PATCH",
            "/participantes/part-001/status",
            json={"status_gravacao": "ja_participei"},
        )
        case_log["output"] = {
            "status_code": response.status_code,
            "body": response.text,
        }
    except Exception as exc:
        case_log["output"] = {
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        raise

    assert response.status_code == 200
    assert response.json()["novo_status"] == "ja_participei"
    assert response.json()["videos_associados"] == ["vid-001"]


@pytest.mark.asyncio
async def test_accept_terms_route_validates_payload_and_missing_participant(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository(),
    )
    monkeypatch.setattr(participantes_router_module, "utc_now", lambda: FIXED_NOW)
    app = build_app(participantes_router_module.router)

    reject_response = await request(
        app,
        "PATCH",
        "/participantes/part-001/aceite-termo",
        json={"aceitou": False, "versao_termo": "v1"},
    )
    missing_response = await request(
        app,
        "PATCH",
        "/participantes/part-001/aceite-termo",
        json={"aceitou": True, "versao_termo": "v1"},
    )

    assert reject_response.status_code == 400
    assert reject_response.json()["detail"] == "O participante deve aceitar o termo para prosseguir."
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_accept_terms_route_records_audit_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(participantes_router_module, "utc_now", lambda: FIXED_NOW)
    app = build_app(participantes_router_module.router)

    response = await request(
        app,
        "PATCH",
        "/participantes/part-001/aceite-termo",
        json={"aceitou": True, "versao_termo": "v2"},
    )

    assert response.status_code == 200
    assert response.json()["auditoria"]["versao_termo"] == "v2"
    assert response.json()["auditoria"]["data_hora_aceite"] == FIXED_NOW.isoformat()


@pytest.mark.asyncio
async def test_accept_terms_route_should_reject_blank_term_version(monkeypatch, case_log) -> None:
    case_log["input"] = {
        "route": "/participantes/part-001/aceite-termo",
        "payload": {"aceitou": True, "versao_termo": "   "},
    }
    case_log["notes"] = [
        "Contrato esperado: o aceite precisa registrar uma versão não vazia do termo.",
    ]

    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(participantes_router_module, "utc_now", lambda: FIXED_NOW)
    app = build_app(participantes_router_module.router)

    response = await request(
        app,
        "PATCH",
        "/participantes/part-001/aceite-termo",
        json={"aceitou": True, "versao_termo": "   "},
    )

    case_log["output"] = {
        "status_code": response.status_code,
        "body": response.text,
    }

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("2026-01-01T12:00:00", datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)),
        ("2026-01-01T12:00:00Z", datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)),
    ],
)
def test_normalize_utc_datetime_handles_supported_inputs(value, expected) -> None:
    assert normalize_utc_datetime(value) == expected


def test_utc_isoformat_falls_back_to_current_time(monkeypatch) -> None:
    monkeypatch.setattr("app.time_utils.utc_now", lambda: FIXED_NOW)

    assert utc_isoformat("invalid") == FIXED_NOW.isoformat()
