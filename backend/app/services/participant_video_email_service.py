from datetime import date, datetime, timezone

from app.schemas.participant_video_email import (
    ParticipantVideoAttachment,
    VideoEmailDispatchRequest,
    VideoEmailDispatchResponse,
)
from app.time_utils import normalize_utc_datetime, utc_now


class ParticipantNotFoundError(ValueError):
    """Raised when the participant does not exist."""


class ParticipantEmailMissingError(ValueError):
    """Raised when the participant record has no email."""


class ParticipantVideoNotFoundError(ValueError):
    """Raised when there is no video registered for the requested date."""  # noqa: D401


class ParticipantVideoUnavailableError(ValueError):
    """Raised when there is a video record for the date but it is not available."""


class ParticipantVideoFileMissingError(ValueError):
    """Raised when the video metadata exists but the file is not stored in MongoDB."""


class ParticipantVideoEmailService:
    """Coordinate participant lookup, video selection, email dispatch, and audit logging."""

    def __init__(
        self,
        participant_repository,
        video_repository,
        participant_video_repository,
        dispatch_repository,
        video_file_repository,
        email_sender,
    ) -> None:
        self._participant_repository = participant_repository
        self._video_repository = video_repository
        self._participant_video_repository = participant_video_repository
        self._dispatch_repository = dispatch_repository
        self._video_file_repository = video_file_repository
        self._email_sender = email_sender

    async def send_video_of_day(
        self,
        participant_id: str,
        request_data: VideoEmailDispatchRequest,
    ) -> VideoEmailDispatchResponse:
        participant = await self._participant_repository.get_by_id(participant_id)

        if participant is None:
            raise ParticipantNotFoundError("Participante não encontrado.")

        participant_email = str(participant.get("email", "")).strip()

        if not self._is_valid_email(participant_email):
            raise ParticipantEmailMissingError(
                "O participante informado não possui um e-mail válido cadastrado."
            )

        selected_video = await self._resolve_selected_video(
            participant_id=participant["id"],
            request_data=request_data,
        )

        if str(selected_video.get("status", "available")) != "available":
            raise ParticipantVideoUnavailableError(
                "O vídeo selecionado ainda não está disponível para envio."
            )

        reference_timestamp = normalize_utc_datetime(selected_video.get("recorded_at")) or utc_now()
        reference_date = reference_timestamp.date()

        file_id = str(selected_video.get("file_id", "")).strip()

        if not file_id:
            raise ParticipantVideoFileMissingError(
                "O vídeo foi localizado, mas o arquivo ainda não foi salvo no banco de dados. "
                "Faça o upload do vídeo antes de enviar por e-mail."
            )

        stored_video_file = await self._video_file_repository.get_file(file_id)

        if stored_video_file is None:
            raise ParticipantVideoFileMissingError(
                "O vídeo foi localizado, mas o arquivo não pôde ser recuperado do banco de dados."
            )

        if stored_video_file.get("video_id") != selected_video["id"]:
            raise ParticipantVideoFileMissingError(
                "O vídeo foi localizado, mas o arquivo salvo no banco de dados "
                "não está vinculado a este vídeo."
            )

        delivery_result = await self._email_sender.send_video_email(
            participant=participant,
            video=selected_video,
            video_file=stored_video_file,
            reference_date=reference_date,
        )

        dispatch_timestamp = utc_now()
        saved_dispatch = await self._dispatch_repository.create(
            {
                "sent_at": dispatch_timestamp,
                "participant_id": participant["id"],
                "participant_email": participant_email,
                "reference_date": reference_date.isoformat(),
                "delivery_mode": delivery_result["delivery_mode"],
                "video_id": selected_video["id"],
            }
        )

        response_message = (
            "Vídeo anexado enviado com sucesso para o e-mail cadastrado."
            if delivery_result["delivery_mode"] == "smtp"
            else (
                "SMTP não configurado. O envio do vídeo anexado foi registrado "
                "na outbox local para validação do fluxo."
            )
        )

        return VideoEmailDispatchResponse(
            dispatch_id=saved_dispatch["id"],
            sent_at=saved_dispatch["sent_at"],
            participant_id=participant["id"],
            participant_email=participant_email,
            reference_date=reference_date,
            delivery_mode=delivery_result["delivery_mode"],
            video=ParticipantVideoAttachment(
                id=selected_video["id"],
                title=selected_video["title"],
                recorded_at=selected_video["recorded_at"],
                filename=stored_video_file["filename"],
                content_type=stored_video_file["content_type"],
                size_bytes=stored_video_file["size_bytes"],
            ),
            message=response_message,
        )

    async def _resolve_selected_video(
        self,
        *,
        participant_id: str,
        request_data: VideoEmailDispatchRequest,
    ) -> dict:
        reference_date = request_data.reference_date or utc_now().date()
        participant_links = await self._participant_video_repository.list_by_participant(
            participant_id
        )
        linked_video_ids = [str(link.get("video_id") or link.get("id") or "") for link in participant_links]
        linked_video_ids = [video_id for video_id in linked_video_ids if video_id]

        if request_data.video_id:
            participant_link = await self._participant_video_repository.get_by_id_and_participant(
                participant_id,
                request_data.video_id,
            )

            if participant_link is None:
                raise ParticipantVideoNotFoundError(
                    "O vídeo selecionado não foi encontrado para o participante."
                )

            selected_video = await self._video_repository.get_by_id(
                str(participant_link.get("video_id") or participant_link.get("id"))
            )

            if selected_video is None:
                raise ParticipantVideoNotFoundError(
                    "O vídeo selecionado não foi encontrado no catálogo principal."
                )

            video_recorded_at = normalize_utc_datetime(selected_video.get("recorded_at")) or utc_now()

            if request_data.reference_date and video_recorded_at.date() != reference_date:
                raise ParticipantVideoNotFoundError(
                    "O vídeo selecionado não corresponde à data informada."
                )

            return selected_video

        linked_videos = await self._video_repository.list_by_ids(linked_video_ids)

        videos_of_day = [
            video
            for video in linked_videos
            if (normalize_utc_datetime(video.get("recorded_at")) or utc_now()).date()
            == reference_date
        ]

        if not videos_of_day:
            raise ParticipantVideoNotFoundError(
                "Nenhum vídeo foi encontrado para o participante na data "
                f"{reference_date.isoformat()}."
            )

        available_videos = [
            video for video in videos_of_day if str(video.get("status", "available")) == "available"
        ]

        if not available_videos:
            raise ParticipantVideoUnavailableError(
                "O vídeo do dia "
                f"{reference_date.isoformat()} ainda não está disponível para envio."
            )

        return max(
            available_videos,
            key=lambda video: normalize_utc_datetime(video.get("recorded_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
        )

    def _is_valid_email(self, value: str) -> bool:
        return "@" in value and not value.startswith("@") and not value.endswith("@")
