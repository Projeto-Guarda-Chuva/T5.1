from datetime import datetime, timedelta
from uuid import uuid4

from app.schemas.video import VideoUploadResponse
from app.time_utils import normalize_utc_datetime, utc_now


class VideoUploadInvalidError(ValueError):
    """Raised when the uploaded payload is invalid."""


class VideoUploadService:
    """Store uploaded videos and associate them automatically to recent participants."""

    def __init__(
        self,
        video_repository,
        video_file_repository,
        participant_recording_event_repository,
        participant_video_repository,
    ) -> None:
        self._video_repository = video_repository
        self._video_file_repository = video_file_repository
        self._participant_recording_event_repository = (
            participant_recording_event_repository
        )
        self._participant_video_repository = participant_video_repository

    async def upload_video(
        self,
        *,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
        title: str | None = None,
        recorded_at: datetime | None = None,
        uploaded_by_email: str | None = None,
    ) -> VideoUploadResponse:
        normalized_filename = (filename or "").strip()

        if not normalized_filename:
            raise VideoUploadInvalidError("O arquivo enviado precisa ter um nome válido.")

        if not file_bytes:
            raise VideoUploadInvalidError("O arquivo enviado está vazio.")

        normalized_content_type = (content_type or "video/mp4").strip().lower()

        if not normalized_content_type.startswith("video/"):
            raise VideoUploadInvalidError("O arquivo enviado precisa ser um vídeo.")

        upload_timestamp = utc_now()
        normalized_recorded_at = normalize_utc_datetime(recorded_at) or upload_timestamp
        video_id = f"vid-{uuid4().hex[:8]}"

        file_data = await self._video_file_repository.replace_file_for_video(
            video_id=video_id,
            filename=normalized_filename,
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )

        video_document = {
            "id": video_id,
            "title": (title or f"Vídeo da participação - {normalized_recorded_at.strftime('%d/%m/%Y %H:%M')}").strip(),
            "status": "available",
            "recorded_at": normalized_recorded_at,
            "uploaded_at": upload_timestamp,
            "uploaded_by_email": uploaded_by_email,
            "duration_seconds": 0,
            "thumbnail_url": "",
            **file_data,
        }

        try:
            saved_video = await self._video_repository.create(video_document)
        except Exception:
            await self._video_file_repository.delete_file(file_data["file_id"])
            raise

        participant_ids = (
            await self._participant_recording_event_repository.list_distinct_participant_ids_between(
                event_type="will_participate",
                start_at=upload_timestamp - timedelta(minutes=30),
                end_at=upload_timestamp,
            )
        )
        associated_participant_ids = (
            await self._participant_video_repository.link_participants_to_video(
                participant_ids=participant_ids,
                video_id=video_id,
                associated_at=upload_timestamp,
                association_source="will_participate_window",
            )
        )

        return VideoUploadResponse(
            id=saved_video["id"],
            title=saved_video["title"],
            recorded_at=saved_video["recorded_at"],
            uploaded_at=saved_video["uploaded_at"],
            filename=saved_video["filename"],
            content_type=saved_video["content_type"],
            size_bytes=saved_video["size_bytes"],
            associated_participant_ids=associated_participant_ids,
            associated_participants_count=len(associated_participant_ids),
            message=(
                "Vídeo enviado com sucesso e associado automaticamente aos participantes elegíveis."
                if associated_participant_ids
                else (
                    "Vídeo enviado com sucesso. Nenhum participante com intenção registrada "
                    "nos últimos 30 minutos foi encontrado para associação automática."
                )
            ),
        )
