from typing import Any


class ParticipantVideoUploadInvalidError(ValueError):
    """Raised when the uploaded file cannot be attached to the participant video."""


class ParticipantVideoStorageService:
    """Replace the binary file of an existing canonical video linked to a participant."""

    def __init__(
        self,
        participant_repository,
        participant_video_repository,
        video_repository,
        video_file_repository,
    ) -> None:
        self._participant_repository = participant_repository
        self._participant_video_repository = participant_video_repository
        self._video_repository = video_repository
        self._video_file_repository = video_file_repository

    async def attach_video_file(
        self,
        participant_id: str,
        video_id: str,
        *,
        filename: str,
        content_type: str | None,
        file_bytes: bytes,
    ) -> dict[str, Any]:
        participant = await self._participant_repository.get_by_id(participant_id)

        if participant is None:
            raise ValueError("Participante não encontrado.")

        participant_video_link = await self._participant_video_repository.get_by_id_and_participant(
            participant_id,
            video_id,
        )

        if participant_video_link is None:
            raise ValueError("Vídeo não encontrado para o participante informado.")

        canonical_video = await self._video_repository.get_by_id(video_id)

        if canonical_video is None:
            raise ValueError("Vídeo não encontrado no catálogo principal.")

        normalized_filename = filename.strip()

        if not normalized_filename:
            raise ParticipantVideoUploadInvalidError(
                "O arquivo enviado precisa ter um nome válido."
            )

        if not file_bytes:
            raise ParticipantVideoUploadInvalidError("O arquivo enviado está vazio.")

        normalized_content_type = (content_type or "video/mp4").strip().lower()

        if not normalized_content_type.startswith("video/"):
            raise ParticipantVideoUploadInvalidError(
                "O arquivo enviado precisa ser um vídeo."
            )

        file_data = await self._video_file_repository.replace_file_for_video(
            video_id=video_id,
            filename=normalized_filename,
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )
        updated_video = await self._video_repository.update_file_metadata(
            video_id,
            file_data,
        )

        if updated_video is None:
            raise ValueError("Não foi possível atualizar o vídeo principal informado.")

        return updated_video
