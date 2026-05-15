from datetime import timedelta
from uuid import uuid4

from app.schemas.participant_recording import ParticipationEventResponse
from app.time_utils import utc_now


class ParticipantRecordingService:
    """Handle participation intent events and automatic video association windows."""

    def __init__(
        self,
        participant_repository,
        event_repository,
        video_repository,
        participant_video_repository,
    ) -> None:
        self._participant_repository = participant_repository
        self._event_repository = event_repository
        self._video_repository = video_repository
        self._participant_video_repository = participant_video_repository

    async def mark_will_participate(
        self,
        participant_id: str,
    ) -> ParticipationEventResponse:
        participant = await self._require_participant(participant_id)
        event_timestamp = utc_now()

        await self._event_repository.create(
            {
                "id": f"prevt-{uuid4().hex[:8]}",
                "participant_id": participant["id"],
                "event_type": "will_participate",
                "created_at": event_timestamp,
            }
        )
        await self._participant_repository.update_fields(
            participant["id"],
            {
                "status_gravacao": "ainda_participarei",
                "status_gravacao_atualizado_em": event_timestamp.isoformat(),
            },
        )

        return ParticipationEventResponse(
            participant_id=participant["id"],
            participant_email=participant["email"],
            event_type="will_participate",
            recorded_at=event_timestamp,
            associated_video_ids=[],
            associated_videos_count=0,
            message=(
                "Participação futura registrada com sucesso. "
                "Os próximos vídeos enviados nos 30 minutos seguintes poderão "
                "ser associados automaticamente."
            ),
        )

    async def mark_already_participated(
        self,
        participant_id: str,
    ) -> ParticipationEventResponse:
        participant = await self._require_participant(participant_id)
        event_timestamp = utc_now()

        await self._event_repository.create(
            {
                "id": f"prevt-{uuid4().hex[:8]}",
                "participant_id": participant["id"],
                "event_type": "already_participated",
                "created_at": event_timestamp,
            }
        )
        await self._participant_repository.update_fields(
            participant["id"],
            {
                "status_gravacao": "ja_participei",
                "status_gravacao_atualizado_em": event_timestamp.isoformat(),
            },
        )

        recent_videos = await self._video_repository.list_uploaded_between(
            event_timestamp - timedelta(hours=1),
            event_timestamp,
        )
        associated_video_ids = sorted(
            {
                str(video["id"])
                for video in recent_videos
                if str(video.get("status", "available")) == "available"
            }
        )

        for video_id in associated_video_ids:
            await self._participant_video_repository.link_participant_to_video(
                participant_id=participant["id"],
                video_id=video_id,
                associated_at=event_timestamp,
                association_source="already_participated_window",
            )

        return ParticipationEventResponse(
            participant_id=participant["id"],
            participant_email=participant["email"],
            event_type="already_participated",
            recorded_at=event_timestamp,
            associated_video_ids=associated_video_ids,
            associated_videos_count=len(associated_video_ids),
            message=(
                "Participação concluída registrada com sucesso. "
                "Os vídeos enviados na última hora foram associados automaticamente."
                if associated_video_ids
                else (
                    "Participação concluída registrada com sucesso. "
                    "Nenhum vídeo enviado na última hora estava disponível para associação."
                )
            ),
        )

    async def register_status(
        self,
        participant_id: str,
        status_gravacao: str,
    ) -> ParticipationEventResponse:
        if status_gravacao == "ainda_participarei":
            return await self.mark_will_participate(participant_id)

        if status_gravacao == "ja_participei":
            return await self.mark_already_participated(participant_id)

        raise ValueError("Status inválido.")

    async def _require_participant(self, participant_id: str) -> dict:
        participant = await self._participant_repository.get_by_id(participant_id)

        if participant is None:
            raise ValueError("Participante não encontrado.")

        return participant
