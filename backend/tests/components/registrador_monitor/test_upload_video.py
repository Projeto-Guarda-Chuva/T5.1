from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.routers import participantes as participantes_router_module
from app.routers import videos as videos_router_module
from app.services.participant_video_storage_service import (
    ParticipantVideoStorageService,
    ParticipantVideoUploadInvalidError,
)
from app.services.video_upload_service import VideoUploadInvalidError, VideoUploadService
from tests.support import (
    FakeDispatchRepository,
    FakeEmailSender,
    FakeEventRepository,
    FakeParticipantRepository,
    FakeParticipantVideoRepository,
    FakeVideoFileRepository,
    FakeVideoRepository,
    build_app,
    request,
)


FIXED_NOW = datetime(2026, 1, 2, 9, 30, tzinfo=timezone.utc)


def _participant(participant_id: str = "part-001", email: str = "participant@example.com") -> dict:
    return {
        "id": participant_id,
        "name": "Participante",
        "email": email,
    }


@pytest.mark.parametrize(
    ("filename", "content_type", "file_bytes", "message"),
    [
        ("", "video/mp4", b"bytes", "nome válido"),
        ("video.mp4", "video/mp4", b"", "está vazio"),
        ("video.mp4", "text/plain", b"bytes", "precisa ser um vídeo"),
    ],
)
@pytest.mark.asyncio
async def test_upload_video_rejects_invalid_payloads(
    filename: str,
    content_type: str,
    file_bytes: bytes,
    message: str,
) -> None:
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(),
        dispatch_repository=FakeDispatchRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(VideoUploadInvalidError) as exc:
        await service.upload_video(
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

    assert message in str(exc.value)


@pytest.mark.asyncio
async def test_upload_video_returns_message_when_no_recent_participants(monkeypatch) -> None:
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository([]),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(),
        dispatch_repository=FakeDispatchRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    response = await service.upload_video(
        filename="video.mp4",
        content_type="video/mp4",
        file_bytes=b"1234",
    )

    assert response.associated_participant_ids == []
    assert "Nenhum participante com intenção registrada" in response.message


@pytest.mark.asyncio
async def test_upload_video_should_fallback_to_generated_title_when_title_is_whitespace(
    monkeypatch,
) -> None:
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(),
        dispatch_repository=FakeDispatchRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    response = await service.upload_video(
        filename="video.mp4",
        content_type="video/mp4",
        file_bytes=b"1234",
        title="   ",
    )

    assert response.title.startswith("Vídeo da participação - ")
    assert response.title.strip()


@pytest.mark.asyncio
async def test_upload_video_associates_recent_participants_and_schedules_email_tasks(monkeypatch) -> None:
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository(["part-001", "part-002"]),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(
            [_participant("part-001"), _participant("part-002", "other@example.com")]
        ),
        dispatch_repository=FakeDispatchRepository(),
        email_sender=FakeEmailSender(),
    )
    scheduled: list = []

    def capture_task(coro):
        scheduled.append(coro)
        return None

    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)
    monkeypatch.setattr("app.services.video_upload_service.asyncio.create_task", capture_task)

    response = await service.upload_video(
        filename="video.mp4",
        content_type="video/mp4",
        file_bytes=b"1234",
    )

    assert response.associated_participant_ids == ["part-001", "part-002"]
    assert response.associated_participants_count == 2
    assert len(scheduled) == 2

    for coro in scheduled:
        coro.close()


@pytest.mark.asyncio
async def test_upload_video_deletes_uploaded_file_when_video_creation_fails(monkeypatch) -> None:
    video_repository = FakeVideoRepository()
    video_repository.raise_on_create = RuntimeError("db down")
    video_file_repository = FakeVideoFileRepository()
    service = VideoUploadService(
        video_repository=video_repository,
        video_file_repository=video_file_repository,
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(),
        dispatch_repository=FakeDispatchRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    with pytest.raises(RuntimeError) as exc:
        await service.upload_video(
            filename="video.mp4",
            content_type="video/mp4",
            file_bytes=b"1234",
        )

    assert str(exc.value) == "db down"
    assert video_file_repository.deleted_file_ids == ["file-1"]


@pytest.mark.asyncio
async def test_send_video_email_safe_ignores_missing_participant(monkeypatch) -> None:
    dispatch_repository = FakeDispatchRepository()
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=FakeParticipantRepository(),
        dispatch_repository=dispatch_repository,
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    await service._send_video_email_safe(
        participant_id="missing",
        saved_video={"id": "vid-001", "recorded_at": FIXED_NOW},
        file_id="file-1",
    )

    assert dispatch_repository.items == []


@pytest.mark.asyncio
async def test_send_video_email_safe_ignores_invalid_email_and_missing_file(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant(email="invalido")])
    video_file_repository = FakeVideoFileRepository()
    dispatch_repository = FakeDispatchRepository()
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=video_file_repository,
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=participant_repository,
        dispatch_repository=dispatch_repository,
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    await service._send_video_email_safe(
        participant_id="part-001",
        saved_video={"id": "vid-001", "recorded_at": FIXED_NOW},
        file_id="missing",
    )

    assert dispatch_repository.items == []


@pytest.mark.asyncio
async def test_send_video_email_safe_ignores_missing_binary_file_for_valid_email(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    dispatch_repository = FakeDispatchRepository()
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=FakeVideoFileRepository(),
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=participant_repository,
        dispatch_repository=dispatch_repository,
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    await service._send_video_email_safe(
        participant_id="part-001",
        saved_video={"id": "vid-001", "recorded_at": FIXED_NOW},
        file_id="missing",
    )

    assert dispatch_repository.items == []


@pytest.mark.asyncio
async def test_send_video_email_safe_records_dispatch_on_success(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    video_file_repository = FakeVideoFileRepository()
    await video_file_repository.replace_file_for_video(
        video_id="vid-001",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    dispatch_repository = FakeDispatchRepository()
    email_sender = FakeEmailSender(delivery_mode="smtp")
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=video_file_repository,
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=participant_repository,
        dispatch_repository=dispatch_repository,
        email_sender=email_sender,
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    await service._send_video_email_safe(
        participant_id="part-001",
        saved_video={"id": "vid-001", "recorded_at": FIXED_NOW, "title": "Vídeo"},
        file_id="file-1",
    )

    assert len(email_sender.calls) == 1
    assert dispatch_repository.items[0]["delivery_mode"] == "smtp"


@pytest.mark.asyncio
async def test_send_video_email_safe_swallows_sender_exceptions(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    video_file_repository = FakeVideoFileRepository()
    await video_file_repository.replace_file_for_video(
        video_id="vid-001",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    email_sender = FakeEmailSender()
    email_sender.raise_error = RuntimeError("smtp down")
    dispatch_repository = FakeDispatchRepository()
    service = VideoUploadService(
        video_repository=FakeVideoRepository(),
        video_file_repository=video_file_repository,
        participant_recording_event_repository=FakeEventRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        participant_repository=participant_repository,
        dispatch_repository=dispatch_repository,
        email_sender=email_sender,
    )
    monkeypatch.setattr("app.services.video_upload_service.utc_now", lambda: FIXED_NOW)

    await service._send_video_email_safe(
        participant_id="part-001",
        saved_video={"id": "vid-001", "recorded_at": FIXED_NOW, "title": "Vídeo"},
        file_id="file-1",
    )

    assert dispatch_repository.items == []


@pytest.mark.parametrize(
    ("participant_exists", "link_exists", "video_exists", "filename", "content_type", "file_bytes", "message"),
    [
        (False, True, True, "video.mp4", "video/mp4", b"1234", "Participante não encontrado."),
        (True, False, True, "video.mp4", "video/mp4", b"1234", "Vídeo não encontrado para o participante informado."),
        (True, True, False, "video.mp4", "video/mp4", b"1234", "Vídeo não encontrado no catálogo principal."),
        (True, True, True, "", "video/mp4", b"1234", "nome válido"),
        (True, True, True, "video.mp4", "video/mp4", b"", "está vazio"),
        (True, True, True, "video.mp4", "text/plain", b"1234", "precisa ser um vídeo"),
    ],
)
@pytest.mark.asyncio
async def test_attach_video_file_validates_all_preconditions(
    participant_exists: bool,
    link_exists: bool,
    video_exists: bool,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    message: str,
) -> None:
    participant_repository = FakeParticipantRepository([_participant()]) if participant_exists else FakeParticipantRepository()
    participant_video_repository = FakeParticipantVideoRepository(
        [{"participant_id": "part-001", "video_id": "vid-001"}] if link_exists else []
    )
    video_repository = FakeVideoRepository(
        [{"id": "vid-001", "title": "Vídeo", "recorded_at": FIXED_NOW}] if video_exists else []
    )
    service = ParticipantVideoStorageService(
        participant_repository=participant_repository,
        participant_video_repository=participant_video_repository,
        video_repository=video_repository,
        video_file_repository=FakeVideoFileRepository(),
    )

    with pytest.raises((ValueError, ParticipantVideoUploadInvalidError)) as exc:
        await service.attach_video_file(
            "part-001",
            "vid-001",
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

    assert message in str(exc.value)


@pytest.mark.asyncio
async def test_attach_video_file_raises_when_main_video_cannot_be_updated() -> None:
    video_repository = FakeVideoRepository([{"id": "vid-001", "title": "Vídeo", "recorded_at": FIXED_NOW}])
    video_repository.update_returns_none = True
    service = ParticipantVideoStorageService(
        participant_repository=FakeParticipantRepository([_participant()]),
        participant_video_repository=FakeParticipantVideoRepository(
            [{"participant_id": "part-001", "video_id": "vid-001"}]
        ),
        video_repository=video_repository,
        video_file_repository=FakeVideoFileRepository(),
    )

    with pytest.raises(ValueError) as exc:
        await service.attach_video_file(
            "part-001",
            "vid-001",
            filename="video.mp4",
            content_type="video/mp4",
            file_bytes=b"1234",
        )

    assert "Não foi possível atualizar o vídeo principal informado." == str(exc.value)


@pytest.mark.asyncio
async def test_attach_video_file_returns_updated_video_metadata() -> None:
    video_repository = FakeVideoRepository(
        [
            {
                "id": "vid-001",
                "title": "Vídeo",
                "recorded_at": FIXED_NOW,
                "filename": "old.mp4",
                "content_type": "video/mp4",
                "size_bytes": 1,
            }
        ]
    )
    service = ParticipantVideoStorageService(
        participant_repository=FakeParticipantRepository([_participant()]),
        participant_video_repository=FakeParticipantVideoRepository(
            [{"participant_id": "part-001", "video_id": "vid-001"}]
        ),
        video_repository=video_repository,
        video_file_repository=FakeVideoFileRepository(),
    )

    updated = await service.attach_video_file(
        "part-001",
        "vid-001",
        filename="video.mp4",
        content_type="video/mp4",
        file_bytes=b"1234",
    )

    assert updated["filename"] == "video.mp4"
    assert updated["size_bytes"] == 4


@pytest.mark.asyncio
async def test_videos_router_returns_current_user_videos(monkeypatch) -> None:
    async def list_user_videos(email: str):
        return {"items": [], "total": 0, "message": "Nenhum vídeo encontrado."}

    monkeypatch.setattr(videos_router_module.video_service, "list_user_videos", list_user_videos)
    app = build_app(videos_router_module.router)

    response = await request(app, "GET", "/videos")

    assert response.status_code == 200
    assert response.json()["message"] == "Nenhum vídeo encontrado."


@pytest.mark.asyncio
async def test_videos_router_maps_invalid_upload_to_http_400(monkeypatch) -> None:
    class StubVideoUploadService:
        async def upload_video(self, **kwargs):
            raise VideoUploadInvalidError("Arquivo inválido.")

    monkeypatch.setattr(videos_router_module, "video_upload_service", StubVideoUploadService())
    app = build_app(videos_router_module.router)

    response = await request(
        app,
        "POST",
        "/videos",
        files={"video": ("video.txt", b"abc", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Arquivo inválido."


@pytest.mark.asyncio
async def test_videos_router_returns_created_payload_for_valid_upload(monkeypatch) -> None:
    class StubVideoUploadService:
        async def upload_video(self, **kwargs):
            return {
                "id": "vid-001",
                "title": "Vídeo",
                "recorded_at": FIXED_NOW,
                "uploaded_at": FIXED_NOW,
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size_bytes": 4,
                "associated_participant_ids": [],
                "associated_participants_count": 0,
                "message": "ok",
            }

    monkeypatch.setattr(videos_router_module, "video_upload_service", StubVideoUploadService())
    app = build_app(videos_router_module.router)

    response = await request(
        app,
        "POST",
        "/videos",
        files={"video": ("video.mp4", b"1234", "video/mp4")},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "vid-001"


@pytest.mark.asyncio
async def test_participant_video_storage_route_maps_errors_and_success(monkeypatch) -> None:
    class StubParticipantVideoStorageService:
        async def attach_video_file(self, participante_id, video_id, **kwargs):
            if video_id == "invalid":
                raise ParticipantVideoUploadInvalidError("Arquivo inválido.")
            if video_id == "missing":
                raise ValueError("Vídeo não encontrado.")
            return {
                "id": video_id,
                "title": "Vídeo",
                "recorded_at": FIXED_NOW,
                "filename": "video.mp4",
                "content_type": "video/mp4",
                "size_bytes": 4,
            }

    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_storage_service",
        StubParticipantVideoStorageService(),
    )
    app = build_app(participantes_router_module.router)

    invalid_response = await request(
        app,
        "POST",
        "/participantes/part-001/videos/invalid/arquivo",
        files={"video": ("video.mp4", b"1234", "video/mp4")},
    )
    missing_response = await request(
        app,
        "POST",
        "/participantes/part-001/videos/missing/arquivo",
        files={"video": ("video.mp4", b"1234", "video/mp4")},
    )
    success_response = await request(
        app,
        "POST",
        "/participantes/part-001/videos/vid-001/arquivo",
        files={"video": ("video.mp4", b"1234", "video/mp4")},
    )

    assert invalid_response.status_code == 400
    assert missing_response.status_code == 404
    assert success_response.status_code == 201
    assert success_response.json()["video"]["id"] == "vid-001"
