from datetime import date, datetime

from app.schemas.participant_video_email import (
    ParticipantVideoAttachment,
    VideoEmailDispatchRequest,
    VideoEmailDispatchResponse,
)


class ParticipantNotFoundError(ValueError):
    """Raised when the participant does not exist."""


class ParticipantEmailMissingError(ValueError):
    """Raised when the participant record has no email."""


class ParticipantVideoNotFoundError(ValueError):
    """Raised when there is no video registered for the requested date."""


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
        dispatch_repository,
        video_file_repository,
        email_sender,
    ) -> None:
        self._participant_repository = participant_repository
        self._video_repository = video_repository
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

        reference_date = request_data.reference_date or date.today()
        videos_of_day = await self._video_repository.list_by_participant_and_date(
            participant_id,
            reference_date,
        )

        if not videos_of_day:
            raise ParticipantVideoNotFoundError(
                "Nenhum vídeo foi encontrado para o participante na data "
                f"{reference_date.isoformat()}."
            )

        available_videos = [
            video for video in videos_of_day if video.get("status") == "available"
        ]

        if not available_videos:
            raise ParticipantVideoUnavailableError(
                "O vídeo do dia "
                f"{reference_date.isoformat()} ainda não está disponível para envio."
            )

        selected_video = max(
            available_videos,
            key=lambda video: self._parse_sortable_datetime(video.get("recorded_at")),
        )

        file_id = str(selected_video.get("file_id", "")).strip()

        if not file_id:
            raise ParticipantVideoFileMissingError(
                "O vídeo foi localizado, mas o arquivo ainda não foi salvo no banco de dados."
            )

        stored_video_file = await self._video_file_repository.get_file(file_id)

        if stored_video_file is None:
            raise ParticipantVideoFileMissingError(
                "O vídeo foi localizado, mas o arquivo não pôde ser recuperado do banco de dados."
            )

        delivery_result = await self._email_sender.send_video_email(
            participant=participant,
            video=selected_video,
            video_file=stored_video_file,
            reference_date=reference_date,
        )

        dispatch_timestamp = datetime.utcnow().replace(microsecond=0).isoformat()
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

    def _is_valid_email(self, value: str) -> bool:
        return "@" in value and not value.startswith("@") and not value.endswith("@")

    def _parse_sortable_datetime(self, value: str | datetime | None) -> datetime:
        if not value:
            return datetime.min

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return datetime.min
