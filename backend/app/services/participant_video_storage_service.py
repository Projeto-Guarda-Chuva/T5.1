from typing import Any


class ParticipantVideoUploadInvalidError(ValueError):
    """Raised when the uploaded file cannot be attached to the participant video."""


class ParticipantVideoStorageService:
    """Store participant video files in GridFS and bind them to a specific video record."""

    def __init__(
        self,
        participant_repository,
        video_repository,
        video_file_repository,
    ) -> None:
        self._participant_repository = participant_repository
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

        video = await self._video_repository.get_by_id_and_participant(
            participant_id,
            video_id,
        )

        if video is None:
            raise ValueError("Vídeo não encontrado para o participante informado.")

        normalized_filename = filename.strip()

        if not normalized_filename:
            raise ParticipantVideoUploadInvalidError(
                "O arquivo enviado precisa ter um nome válido."
            )

        if not file_bytes:
            raise ParticipantVideoUploadInvalidError(
                "O arquivo enviado está vazio."
            )

        normalized_content_type = (content_type or "video/mp4").strip().lower()

        if not normalized_content_type.startswith("video/"):
            raise ParticipantVideoUploadInvalidError(
                "O arquivo enviado precisa ser um vídeo."
            )

        file_data = await self._video_file_repository.replace_file_for_video(
            participant_id=participant_id,
            video_id=video_id,
            filename=normalized_filename,
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )
        await self._video_repository.attach_file_to_video(
            participant_id,
            video_id,
            file_data,
        )

        video["file_id"] = file_data["file_id"]
        video["filename"] = file_data["filename"]
        video["content_type"] = file_data["content_type"]
        video["size_bytes"] = file_data["size_bytes"]

        return video
