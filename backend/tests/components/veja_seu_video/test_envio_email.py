from __future__ import annotations

import asyncio
import smtplib
from datetime import date, datetime, timezone
from email.message import EmailMessage
from types import SimpleNamespace

import pytest

from app.config import Settings, settings
from app.routers import participantes as participantes_router_module
from app.services.participant_video_email_service import (
    ParticipantEmailMissingError,
    ParticipantNotFoundError,
    ParticipantVideoEmailService,
    ParticipantVideoFileMissingError,
    ParticipantVideoNotFoundError,
    ParticipantVideoUnavailableError,
)
from app.services.video_email_sender import EmailDeliveryError, VideoEmailSender
from tests.support import (
    FakeDispatchRepository,
    FakeEmailSender,
    FakeParticipantRepository,
    FakeParticipantVideoRepository,
    FakeVideoFileRepository,
    FakeVideoRepository,
    build_app,
    request,
)


FIXED_NOW = datetime(2026, 1, 5, 14, 0, tzinfo=timezone.utc)


def _participant(participant_id: str = "part-001", email: str = "participant@example.com") -> dict:
    return {
        "id": participant_id,
        "name": "Participante",
        "email": email,
    }


def _video(
    video_id: str,
    *,
    status: str = "available",
    recorded_at: datetime = FIXED_NOW,
    file_id: str = "file-1",
) -> dict:
    return {
        "id": video_id,
        "title": f"Vídeo {video_id}",
        "status": status,
        "recorded_at": recorded_at,
        "file_id": file_id,
    }


@pytest.mark.asyncio
async def test_send_video_of_day_requires_existing_participant_and_valid_email(monkeypatch) -> None:
    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository(),
        video_repository=FakeVideoRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantNotFoundError):
        await service.send_video_of_day(
            "missing",
            SimpleNamespace(reference_date=None, video_id=None),
        )

    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant(email="invalido")]),
        video_repository=FakeVideoRepository(),
        participant_video_repository=FakeParticipantVideoRepository(),
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantEmailMissingError):
        await service.send_video_of_day(
            "part-001",
            SimpleNamespace(reference_date=None, video_id=None),
        )


@pytest.mark.asyncio
async def test_resolve_selected_video_validates_explicit_video_identifier(monkeypatch) -> None:
    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository([_video("vid-001")]),
        participant_video_repository=FakeParticipantVideoRepository(),
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    with pytest.raises(ParticipantVideoNotFoundError) as missing_link_exc:
        await service._resolve_selected_video(
            participant_id="part-001",
            request_data=SimpleNamespace(video_id="vid-001", reference_date=None),
        )

    assert "não foi encontrado para o participante" in str(missing_link_exc.value)


@pytest.mark.asyncio
async def test_resolve_selected_video_handles_missing_canonical_video_and_date_mismatch(monkeypatch) -> None:
    links = FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}])
    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository(),
        participant_video_repository=links,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    with pytest.raises(ParticipantVideoNotFoundError) as missing_video_exc:
        await service._resolve_selected_video(
            participant_id="part-001",
            request_data=SimpleNamespace(video_id="vid-001", reference_date=None),
        )

    assert "catálogo principal" in str(missing_video_exc.value)

    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository([_video("vid-001", recorded_at=FIXED_NOW)]),
        participant_video_repository=links,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoNotFoundError) as mismatch_exc:
        await service._resolve_selected_video(
            participant_id="part-001",
            request_data=SimpleNamespace(video_id="vid-001", reference_date=date(2026, 1, 6)),
        )

    assert "não corresponde à data informada" in str(mismatch_exc.value)


@pytest.mark.asyncio
async def test_resolve_selected_video_for_day_handles_missing_and_unavailable_cases(monkeypatch) -> None:
    links = FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}])
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository([_video("vid-001", recorded_at=datetime(2026, 1, 4, 9, 0, tzinfo=timezone.utc))]),
        participant_video_repository=links,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoNotFoundError) as missing_day_exc:
        await service._resolve_selected_video(
            participant_id="part-001",
            request_data=SimpleNamespace(video_id=None, reference_date=date(2026, 1, 5)),
        )

    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository([_video("vid-001", status="processing", recorded_at=FIXED_NOW)]),
        participant_video_repository=links,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoUnavailableError) as unavailable_exc:
        await service._resolve_selected_video(
            participant_id="part-001",
            request_data=SimpleNamespace(video_id=None, reference_date=date(2026, 1, 5)),
        )

    assert "Nenhum vídeo foi encontrado" in str(missing_day_exc.value)
    assert "ainda não está disponível" in str(unavailable_exc.value)


@pytest.mark.asyncio
async def test_resolve_selected_video_selects_latest_available_video_of_day(monkeypatch) -> None:
    service = ParticipantVideoEmailService(
        participant_repository=FakeParticipantRepository([_participant()]),
        video_repository=FakeVideoRepository(
            [
                _video("vid-001", recorded_at=datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)),
                _video("vid-002", recorded_at=datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)),
                _video("vid-003", status="processing", recorded_at=datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)),
            ]
        ),
        participant_video_repository=FakeParticipantVideoRepository(
            [
                {"participant_id": "part-001", "video_id": "vid-001"},
                {"participant_id": "part-001", "video_id": "vid-002"},
                {"participant_id": "part-001", "video_id": "vid-003"},
            ]
        ),
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    selected = await service._resolve_selected_video(
        participant_id="part-001",
        request_data=SimpleNamespace(video_id=None, reference_date=date(2026, 1, 5)),
    )

    assert selected["id"] == "vid-002"


@pytest.mark.asyncio
async def test_send_video_of_day_maps_unavailable_and_missing_file_scenarios(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    participant_video_repository = FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}])
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    unavailable_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=FakeVideoRepository([_video("vid-001", status="processing")]),
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoUnavailableError):
        await unavailable_service.send_video_of_day(
            "part-001",
            SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
        )

    missing_file_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=FakeVideoRepository([_video("vid-001", file_id="")]),
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoFileMissingError):
        await missing_file_service.send_video_of_day(
            "part-001",
            SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
        )


@pytest.mark.asyncio
async def test_send_video_of_day_detects_missing_or_mismatched_binary_file(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    participant_video_repository = FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}])
    video_repository = FakeVideoRepository([_video("vid-001", file_id="file-1")])
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    missing_file_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=video_repository,
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=FakeVideoFileRepository(),
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoFileMissingError):
        await missing_file_service.send_video_of_day(
            "part-001",
            SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
        )

    file_repository = FakeVideoFileRepository()
    await file_repository.replace_file_for_video(
        video_id="other-video",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    mismatched_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=video_repository,
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=file_repository,
        email_sender=FakeEmailSender(),
    )

    with pytest.raises(ParticipantVideoFileMissingError):
        await mismatched_service.send_video_of_day(
            "part-001",
            SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
        )


@pytest.mark.asyncio
async def test_send_video_of_day_returns_dispatch_payload_for_smtp_and_outbox(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    participant_video_repository = FakeParticipantVideoRepository([{"participant_id": "part-001", "video_id": "vid-001"}])
    video_repository = FakeVideoRepository([_video("vid-001", file_id="file-1")])
    file_repository = FakeVideoFileRepository()
    await file_repository.replace_file_for_video(
        video_id="vid-001",
        filename="video.mp4",
        file_bytes=b"1234",
        content_type="video/mp4",
    )
    monkeypatch.setattr("app.services.participant_video_email_service.utc_now", lambda: FIXED_NOW)

    smtp_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=video_repository,
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=file_repository,
        email_sender=FakeEmailSender(delivery_mode="smtp"),
    )
    outbox_service = ParticipantVideoEmailService(
        participant_repository=participant_repository,
        video_repository=video_repository,
        participant_video_repository=participant_video_repository,
        dispatch_repository=FakeDispatchRepository(),
        video_file_repository=file_repository,
        email_sender=FakeEmailSender(delivery_mode="outbox"),
    )

    smtp_response = await smtp_service.send_video_of_day(
        "part-001",
        SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
    )
    outbox_response = await outbox_service.send_video_of_day(
        "part-001",
        SimpleNamespace(reference_date=date(2026, 1, 5), video_id="vid-001"),
    )

    assert smtp_response.delivery_mode == "smtp"
    assert "enviado com sucesso" in smtp_response.message
    assert outbox_response.delivery_mode == "outbox"
    assert "outbox local" in outbox_response.message


@pytest.mark.asyncio
async def test_video_email_sender_queues_outbox_when_smtp_is_not_configured(monkeypatch) -> None:
    class OutboxRepository:
        def __init__(self) -> None:
            self.items = []

        async def create(self, payload: dict) -> None:
            self.items.append(dict(payload))

    outbox_repository = OutboxRepository()
    sender = VideoEmailSender(outbox_repository)
    monkeypatch.setattr("app.services.video_email_sender.utc_now", lambda: FIXED_NOW)
    monkeypatch.setattr(sender, "_smtp_is_configured", lambda: False)

    result = await sender.send_video_email(
        participant=_participant(),
        video=_video("vid-001", file_id="file-1"),
        video_file={
            "content": b"1234",
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 4,
            "file_id": "file-1",
        },
        reference_date=date(2026, 1, 5),
    )

    assert result["delivery_mode"] == "outbox"
    assert outbox_repository.items[0]["attachment_filename"] == "video.mp4"


@pytest.mark.asyncio
async def test_video_email_sender_uses_smtp_when_configured(monkeypatch) -> None:
    sender = VideoEmailSender(FakeDispatchRepository())
    captured = {"message": None}

    async def fake_to_thread(func, message):
        captured["message"] = message
        func(message)

    monkeypatch.setattr(sender, "_smtp_is_configured", lambda: True)
    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(sender, "_send_via_smtp", lambda message: captured.update(message=message))

    result = await sender.send_video_email(
        participant=_participant(),
        video=_video("vid-001", file_id="file-1"),
        video_file={
            "content": b"1234",
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 4,
            "file_id": "file-1",
        },
        reference_date=date(2026, 1, 5),
    )

    assert result["delivery_mode"] == "smtp"
    assert captured["message"]["To"] == "participant@example.com"


@pytest.mark.asyncio
async def test_video_email_sender_can_queue_non_multipart_messages(monkeypatch) -> None:
    class OutboxRepository:
        def __init__(self) -> None:
            self.items = []

        async def create(self, payload: dict) -> None:
            self.items.append(dict(payload))

    outbox_repository = OutboxRepository()
    sender = VideoEmailSender(outbox_repository)
    monkeypatch.setattr("app.services.video_email_sender.utc_now", lambda: FIXED_NOW)

    message = EmailMessage()
    message["Subject"] = "Assunto"
    message.set_content("Corpo simples")

    await sender._queue_in_outbox(
        message,
        _participant(),
        _video("vid-001"),
        {
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 0,
            "file_id": "file-1",
        },
        date(2026, 1, 5),
    )

    assert outbox_repository.items[0]["subject"] == message["Subject"]


def test_video_email_sender_send_via_smtp_supports_starttls_and_login(monkeypatch) -> None:
    class SMTPStub:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout
            self.started_tls = False
            self.logged_in = None
            self.sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def starttls(self) -> None:
            self.started_tls = True

        def login(self, username: str, password: str) -> None:
            self.logged_in = (username, password)

        def send_message(self, message) -> None:
            self.sent = True

    smtp_stub = SMTPStub("host", 587, 120)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "from@example.com")
    monkeypatch.setattr(settings, "SMTP_USERNAME", "user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pass")
    monkeypatch.setattr(settings, "SMTP_USE_STARTTLS", True)
    monkeypatch.setattr("app.services.video_email_sender.smtplib.SMTP", lambda *args, **kwargs: smtp_stub)
    sender = VideoEmailSender(FakeDispatchRepository())

    message = sender._build_message(
        participant=_participant(),
        video=_video("vid-001"),
        video_file={
            "content": b"1234",
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 4,
            "file_id": "file-1",
        },
        reference_date=date(2026, 1, 5),
    )
    sender._send_via_smtp(message)

    assert smtp_stub.started_tls is True
    assert smtp_stub.logged_in == ("user", "pass")
    assert smtp_stub.sent is True


def test_video_email_sender_send_via_smtp_skips_starttls_and_login_when_not_configured(monkeypatch) -> None:
    class SMTPStub:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.started_tls = False
            self.logged_in = False
            self.sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def starttls(self) -> None:
            self.started_tls = True

        def login(self, username: str, password: str) -> None:
            self.logged_in = True

        def send_message(self, message) -> None:
            self.sent = True

    smtp_stub = SMTPStub("host", 587, 120)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "from@example.com")
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "MAIL_USERNAME", None)
    monkeypatch.setattr(settings, "MAIL_STARTTLS", None)
    monkeypatch.setattr(settings, "SMTP_USE_STARTTLS", False)
    monkeypatch.setattr("app.services.video_email_sender.smtplib.SMTP", lambda *args, **kwargs: smtp_stub)
    sender = VideoEmailSender(FakeDispatchRepository())
    message = sender._build_message(
        participant=_participant(),
        video=_video("vid-001"),
        video_file={
            "content": b"1234",
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 4,
            "file_id": "file-1",
        },
        reference_date=date(2026, 1, 5),
    )

    sender._send_via_smtp(message)

    assert smtp_stub.started_tls is False
    assert smtp_stub.logged_in is False
    assert smtp_stub.sent is True


def test_video_email_sender_maps_smtp_errors(monkeypatch) -> None:
    class SMTPRaisingStub:
        def __init__(self, *args, **kwargs) -> None:
            return None

        def __enter__(self):
            raise smtplib.SMTPException("boom")

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "from@example.com")
    monkeypatch.setattr("app.services.video_email_sender.smtplib.SMTP", lambda *args, **kwargs: SMTPRaisingStub())
    sender = VideoEmailSender(FakeDispatchRepository())
    message = sender._build_message(
        participant=_participant(),
        video=_video("vid-001"),
        video_file={
            "content": b"1234",
            "filename": "video.mp4",
            "content_type": "video/mp4",
            "size_bytes": 4,
            "file_id": "file-1",
        },
        reference_date=date(2026, 1, 5),
    )

    with pytest.raises(EmailDeliveryError):
        sender._send_via_smtp(message)


@pytest.mark.parametrize(
    ("recorded_at", "expected"),
    [
        (None, "Horário não informado"),
        (datetime(2026, 1, 5, 10, 30), "05/01/2026 às 10:30"),
        ("2026-01-05T10:30:00", "05/01/2026 às 10:30"),
        ("valor-invalido", "valor-invalido"),
    ],
)
def test_video_email_sender_formats_recorded_at_values(recorded_at, expected) -> None:
    sender = VideoEmailSender(FakeDispatchRepository())

    assert sender._format_recorded_at(recorded_at) == expected


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        ("video/mp4", ("video", "mp4")),
        ("invalid", ("application", "octet-stream")),
    ],
)
def test_video_email_sender_splits_content_type(content_type: str, expected: tuple[str, str]) -> None:
    sender = VideoEmailSender(FakeDispatchRepository())

    assert sender._split_content_type(content_type) == expected


@pytest.mark.parametrize(
    ("size_bytes", "expected"),
    [
        (512, "512 B"),
        (2048, "2.0 KB"),
        (2 * 1024 * 1024, "2.0 MB"),
    ],
)
def test_video_email_sender_formats_sizes(size_bytes: int, expected: str) -> None:
    sender = VideoEmailSender(FakeDispatchRepository())

    assert sender._format_size_bytes(size_bytes) == expected


def test_settings_resolve_smtp_fallback_properties(case_log, monkeypatch) -> None:
    for env_key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_USE_STARTTLS",
        "MAIL_SERVER",
        "MAIL_PORT",
        "MAIL_USERNAME",
        "MAIL_PASSWORD",
        "MAIL_FROM",
        "MAIL_STARTTLS",
    ):
        monkeypatch.delenv(env_key, raising=False)

    case_log["input"] = {
        "gmail_settings": {"MAIL_FROM": "user@gmail.com"},
        "mail_settings": {
            "MAIL_SERVER": "mail.example.com",
            "MAIL_PORT": 2525,
            "MAIL_USERNAME": "user",
            "MAIL_PASSWORD": "pass",
            "MAIL_FROM": "from@example.com",
            "MAIL_STARTTLS": False,
        },
        "blank_settings": {"MONGODB_URL": "mongodb://localhost:27017"},
    }
    gmail_settings = Settings(_env_file=None, MONGODB_URL="mongodb://localhost:27017", MAIL_FROM="user@gmail.com")
    mail_settings = Settings(
        _env_file=None,
        MONGODB_URL="mongodb://localhost:27017",
        MAIL_SERVER="mail.example.com",
        MAIL_PORT=2525,
        MAIL_USERNAME="user",
        MAIL_PASSWORD="pass",
        MAIL_FROM="from@example.com",
        MAIL_STARTTLS=False,
    )

    assert gmail_settings.resolved_smtp_host == "smtp.gmail.com"
    assert mail_settings.resolved_smtp_host == "mail.example.com"
    assert mail_settings.resolved_smtp_port == 2525
    assert mail_settings.resolved_smtp_username == "user"
    assert mail_settings.resolved_smtp_password == "pass"
    assert mail_settings.resolved_smtp_from_email == "from@example.com"
    assert mail_settings.resolved_smtp_use_starttls is False
    blank_settings = Settings(_env_file=None, MONGODB_URL="mongodb://localhost:27017")
    case_log["output"] = {
        "resolved_smtp_host": blank_settings.resolved_smtp_host,
        "resolved_smtp_port": blank_settings.resolved_smtp_port,
        "resolved_smtp_use_starttls": blank_settings.resolved_smtp_use_starttls,
    }
    assert blank_settings.resolved_smtp_host is None
    assert blank_settings.resolved_smtp_port == 587
    assert blank_settings.resolved_smtp_use_starttls is True


def test_video_email_sender_resolves_participant_name_and_smtp_flag(monkeypatch) -> None:
    sender = VideoEmailSender(FakeDispatchRepository())
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "MAIL_SERVER", None)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", None)
    monkeypatch.setattr(settings, "MAIL_FROM", None)

    assert sender._resolve_participant_name({"nome": " Nome "}) == "Nome"
    assert sender._smtp_is_configured() is False


@pytest.mark.asyncio
async def test_email_routes_map_service_errors_and_success(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    monkeypatch.setattr(participantes_router_module, "participant_repository", participant_repository)

    class StubParticipantVideoEmailService:
        async def send_video_of_day(self, participant_id: str, envio):
            if participant_id == "part-email":
                raise ParticipantEmailMissingError("email")
            if participant_id == "part-video":
                raise ParticipantVideoNotFoundError("video")
            if participant_id == "part-unavailable":
                raise ParticipantVideoUnavailableError("unavailable")
            if participant_id == "part-file":
                raise ParticipantVideoFileMissingError("file")
            if participant_id == "part-delivery":
                raise EmailDeliveryError("delivery")
            if participant_id == "missing":
                raise ParticipantNotFoundError("missing")
            return {
                "dispatch_id": "dispatch-1",
                "sent_at": FIXED_NOW,
                "participant_id": participant_id,
                "participant_email": "participant@example.com",
                "reference_date": date(2026, 1, 5),
                "delivery_mode": "outbox",
                "video": {
                    "id": "vid-001",
                    "title": "Vídeo",
                    "recorded_at": FIXED_NOW,
                    "filename": "video.mp4",
                    "content_type": "video/mp4",
                    "size_bytes": 4,
                },
                "message": "ok",
            }

    monkeypatch.setattr(
        participantes_router_module,
        "participant_video_email_service",
        StubParticipantVideoEmailService(),
    )
    app = build_app(participantes_router_module.router, current_user="participant@example.com")

    success_response = await request(
        app,
        "POST",
        "/participantes/me/video-do-dia/email",
        json={},
    )
    missing_current_participant_app = build_app(participantes_router_module.router, current_user="missing@example.com")
    missing_current_participant_response = await request(
        missing_current_participant_app,
        "POST",
        "/participantes/me/video-do-dia/email",
        json={},
    )
    email_error_response = await request(app, "POST", "/participantes/part-email/video-do-dia/email", json={})
    video_error_response = await request(app, "POST", "/participantes/part-video/video-do-dia/email", json={})
    unavailable_response = await request(app, "POST", "/participantes/part-unavailable/video-do-dia/email", json={})
    file_error_response = await request(app, "POST", "/participantes/part-file/video-do-dia/email", json={})
    delivery_error_response = await request(app, "POST", "/participantes/part-delivery/video-do-dia/email", json={})
    missing_response = await request(app, "POST", "/participantes/missing/video-do-dia/email", json={})

    assert success_response.status_code == 200
    assert missing_current_participant_response.status_code == 404
    assert email_error_response.status_code == 400
    assert video_error_response.status_code == 404
    assert unavailable_response.status_code == 409
    assert file_error_response.status_code == 409
    assert delivery_error_response.status_code == 502
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_current_user_email_route_maps_service_errors(monkeypatch) -> None:
    participant_repository = FakeParticipantRepository([_participant()])
    monkeypatch.setattr(participantes_router_module, "participant_repository", participant_repository)

    class StubParticipantVideoEmailService:
        def __init__(self, error):
            self.error = error

        async def send_video_of_day(self, participant_id: str, envio):
            raise self.error

    errors = [
        (ParticipantEmailMissingError("email"), 400),
        (ParticipantVideoNotFoundError("video"), 404),
        (ParticipantVideoUnavailableError("unavailable"), 409),
        (ParticipantVideoFileMissingError("file"), 409),
        (EmailDeliveryError("delivery"), 502),
    ]

    for error, status_code in errors:
        monkeypatch.setattr(
            participantes_router_module,
            "participant_video_email_service",
            StubParticipantVideoEmailService(error),
        )
        app = build_app(participantes_router_module.router, current_user="participant@example.com")
        response = await request(app, "POST", "/participantes/me/video-do-dia/email", json={})
        assert response.status_code == status_code
