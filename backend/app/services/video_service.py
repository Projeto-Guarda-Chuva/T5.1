from datetime import datetime

from fastapi import HTTPException

from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.schemas.video import VideoClaimRequest, VideoClaimResponse, VideoListResponse


participant_repository = ParticipantRepository()
participant_video_repository = ParticipantVideoRepository()


async def list_user_videos(email: str) -> VideoListResponse:
    participant = await participant_repository.get_by_email(email)

    if participant is None:
        return VideoListResponse(
            items=[],
            total=0,
            message="Nenhum vídeo encontrado.",
        )

    videos = await participant_video_repository.list_by_participant(participant["id"])
    items = [_build_video_response(video) for video in videos]

    return VideoListResponse(
        items=items,
        total=len(items),
        message="Videos retrieved successfully." if items else "Nenhum vídeo encontrado.",
    )


async def claim_video(user_email: str, request: VideoClaimRequest) -> VideoClaimResponse:
    raise HTTPException(
        status_code=501,
        detail=(
            "O fluxo antigo de associação de vídeos de teste foi desativado. "
            "Os vídeos agora precisam ser cadastrados e armazenados no MongoDB."
        ),
    )


def _build_video_response(video: dict) -> dict:
    recorded_at = _normalize_datetime_string(video.get("recorded_at"))

    return {
        "id": video["id"],
        "participant_video_id": video["id"],
        "title": video.get("title", "Vídeo da participação"),
        "created_at": recorded_at,
        "duration_seconds": int(video.get("duration_seconds", 0) or 0),
        "thumbnail_url": str(video.get("thumbnail_url", "") or ""),
        "video_url": "",
        "status": str(video.get("status", "available")),
    }


def _normalize_datetime_string(value: str | datetime | None) -> str:
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat()

    if isinstance(value, str) and value.strip():
        return value

    return datetime.utcnow().replace(microsecond=0).isoformat()
