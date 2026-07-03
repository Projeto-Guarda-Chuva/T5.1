from __future__ import annotations

from datetime import datetime, timezone

import pytest

import main as main_module
from app.routers import participantes as participantes_router_module
from app.routers import videos as videos_router_module
from app.services import video_service as video_service_module
from app.time_utils import normalize_utc_datetime, utc_isoformat, utc_now
from tests.support import (
    FakeParticipantRepository,
    FakeParticipantVideoRepository,
    FakeVideoFileRepository,
    FakeVideoRepository,
    build_app,
    request,
)


FIXED_NOW = datetime(2026, 1, 4, 10, 0, tzinfo=timezone.utc)


def _participant(participant_id: str = "part-001", email: str = "participant@example.com") -> dict:
    return {
        "id": participant_id,
        "name": "Participante",
        "email": email,
    }


def _video(
    video_id: str,
    *,
    recorded_at: datetime | str = FIXED_NOW,
    uploaded_at: datetime | str = FIXED_NOW,
    status: str = "available",
    file_id: str = "",
) -> dict:
    return {
        "id": video_id,
        "title": f"Vídeo {video_id}",
        "recorded_at": recorded_at,
        "uploaded_at": uploaded_at,
        "duration_seconds": 10,
        "thumbnail_url": "thumb.png",
        "status": status,
        "file_id": file_id,
    }


@pytest.mark.asyncio
async def test_list_user_videos_returns_empty_when_participant_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(video_service_module, "participant_repository", FakeParticipantRepository())

    response = await video_service_module.list_user_videos("missing@example.com")

    assert response.total == 0
    assert response.message == "Nenhum vídeo encontrado."


@pytest.mark.asyncio
async def test_list_participant_videos_filters_duplicates_missing_videos_and_sorts_desc(monkeypatch) -> None:
    monkeypatch.setattr(
        video_service_module,
        "participant_video_repository",
        FakeParticipantVideoRepository(
            [
                {"participant_id": "part-001", "video_id": "vid-001"},
                {"participant_id": "part-001", "video_id": "vid-002"},
                {"participant_id": "part-001", "video_id": "vid-002"},
                {"participant_id": "part-001", "video_id": "vid-missing"},
            ]
        ),
    )
    monkeypatch.setattr(
        video_service_module,
        "video_repository",
        FakeVideoRepository(
            [
                _video("vid-001", recorded_at="2026-01-04T09:00:00+00:00"),
                _video("vid-002", recorded_at="2026-01-04T11:00:00+00:00"),
            ]
        ),
    )

    response = await video_service_module.list_participant_videos("part-001")

    assert response.total == 2
    assert [item.id for item in response.items] == ["vid-002", "vid-001"]


@pytest.mark.asyncio
async def test_list_user_videos_returns_participant_videos_when_participant_exists(monkeypatch) -> None:
    monkeypatch.setattr(
        video_service_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        video_service_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(
        video_service_module,
        "video_repository",
        FakeVideoRepository([_video("vid-001")]),
    )

    response = await video_service_module.list_user_videos("participant@example.com")

    assert response.total == 1
    assert response.items[0].id == "vid-001"


@pytest.mark.asyncio
async def test_list_participant_videos_returns_empty_when_no_links_exist(monkeypatch) -> None:
    monkeypatch.setattr(
        video_service_module,
        "participant_video_repository",
        FakeParticipantVideoRepository(),
    )

    response = await video_service_module.list_participant_videos("part-001")

    assert response.total == 0


def test_video_service_normalizes_fallback_datetime(monkeypatch) -> None:
    monkeypatch.setattr(video_service_module, "utc_now", lambda: FIXED_NOW)

    assert video_service_module._normalize_datetime_string("invalid") == FIXED_NOW.isoformat()
    assert video_service_module._build_video_response(_video("vid-001", recorded_at=None))["created_at"]


@pytest.mark.asyncio
async def test_videos_routes_proxy_listing_calls(monkeypatch) -> None:
    async def list_user_videos(email: str):
        return {
            "items": [],
            "total": 0,
            "message": "Nenhum vídeo encontrado.",
        }

    monkeypatch.setattr(videos_router_module.video_service, "list_user_videos", list_user_videos)
    app = build_app(videos_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/videos")
    alias_response = await request(app, "GET", "/videos/meus-videos")

    assert response.status_code == 200
    assert alias_response.status_code == 200
    assert alias_response.json()["message"] == "Nenhum vídeo encontrado."


@pytest.mark.asyncio
async def test_current_participant_route_returns_profile_or_404(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    success_response = await request(app, "GET", "/participantes/me")

    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository(),
    )
    missing_app = build_app(participantes_router_module.router, current_user="missing@example.com")
    missing_response = await request(missing_app, "GET", "/participantes/me")

    assert success_response.status_code == 200
    assert success_response.json()["email"] == "participant@example.com"
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_listar_videos_do_participante_route_maps_missing_participant_and_success(monkeypatch) -> None:
    async def list_participant_videos(participant_id: str):
        return {"items": [], "total": 0, "message": "Nenhum vídeo encontrado."}

    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(participantes_router_module.video_service, "list_participant_videos", list_participant_videos)
    app = build_app(participantes_router_module.router, current_user="admin@example.com")

    success_response = await request(app, "GET", "/participantes/part-001/videos")
    missing_response = await request(app, "GET", "/participantes/missing/videos")

    assert success_response.status_code == 200
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_current_participant_video_file_route_handles_missing_participant(monkeypatch) -> None:
    monkeypatch.setattr(participantes_router_module, "participant_repository", FakeParticipantRepository())
    app = build_app(participantes_router_module.router, current_user="missing@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participante não encontrado."


@pytest.mark.asyncio
async def test_current_participant_video_file_route_handles_missing_link(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository(),
    )
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vídeo não encontrado para o participante."


@pytest.mark.asyncio
async def test_current_participant_video_file_route_handles_missing_canonical_video(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(participantes_router_module, "video_repository", FakeVideoRepository())
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 404
    assert response.json()["detail"] == "Vídeo não encontrado no catálogo principal."


@pytest.mark.asyncio
async def test_current_participant_video_file_route_handles_missing_file_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "video_repository",
        FakeVideoRepository([_video("vid-001", file_id="")]),
    )
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 404
    assert "ainda não foi salvo" in response.json()["detail"]


@pytest.mark.asyncio
async def test_current_participant_video_file_route_handles_missing_binary_file(monkeypatch) -> None:
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "video_repository",
        FakeVideoRepository([_video("vid-001", file_id="file-1")]),
    )
    monkeypatch.setattr(participantes_router_module, "video_file_repository", FakeVideoFileRepository())
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 404
    assert "não pôde ser recuperado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_current_participant_video_file_route_detects_mismatched_file_binding(monkeypatch) -> None:
    file_repository = FakeVideoFileRepository()
    await file_repository.replace_file_for_video(
        video_id="other-video",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "video_repository",
        FakeVideoRepository([_video("vid-001", file_id="file-1")]),
    )
    monkeypatch.setattr(participantes_router_module, "video_file_repository", file_repository)
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 409
    assert "não está vinculado" in response.json()["detail"]


@pytest.mark.asyncio
async def test_current_participant_video_file_route_returns_binary_content(monkeypatch) -> None:
    file_repository = FakeVideoFileRepository()
    await file_repository.replace_file_for_video(
        video_id="vid-001",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_repository",
        FakeParticipantRepository([_participant()]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_repository",
        FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}]),
    )
    monkeypatch.setattr(
        participantes_router_module,
        "video_repository",
        FakeVideoRepository([_video("vid-001", file_id="file-1")]),
    )
    monkeypatch.setattr(participantes_router_module, "video_file_repository", file_repository)
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    response = await request(app, "GET", "/participantes/me/videos/vid-001/arquivo")

    assert response.status_code == 200
    assert response.content == b"1234"
    assert response.headers["content-disposition"] == 'inline; filename="video.mp4"'


@pytest.mark.asyncio
async def test_root_endpoint_returns_running_message() -> None:
    assert await main_module.read_root() == {"message": "T5.1 API running"}


def test_time_utils_cover_additional_datetime_branches(monkeypatch) -> None:
    naive_datetime = datetime(2026, 1, 4, 10, 0)

    assert normalize_utc_datetime(naive_datetime) == naive_datetime.replace(tzinfo=timezone.utc)
    assert normalize_utc_datetime(123) is None
    assert utc_isoformat(naive_datetime) == naive_datetime.replace(tzinfo=timezone.utc).isoformat()
    assert utc_now().tzinfo == timezone.utc
