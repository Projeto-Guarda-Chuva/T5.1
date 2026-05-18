from datetime import datetime, timezone

from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoListResponse
from app.time_utils import normalize_utc_datetime, utc_now


participant_repository = ParticipantRepository()
participant_video_repository = ParticipantVideoRepository()
video_repository = VideoRepository()


async def list_user_videos(email: str) -> VideoListResponse:
    participant = await participant_repository.get_by_email(email)

    if participant is None:
        return VideoListResponse(
            items=[],
            total=0,
            message="Nenhum vídeo encontrado.",
        )

    return await list_participant_videos(participant["id"])


async def list_participant_videos(participant_id: str) -> VideoListResponse:
    participant_links = await participant_video_repository.list_by_participant(participant_id)

    if not participant_links:
        return VideoListResponse(
            items=[],
            total=0,
            message="Nenhum vídeo encontrado.",
        )

    linked_video_ids = [
        str(link.get("video_id") or link.get("id") or "")
        for link in participant_links
        if str(link.get("video_id") or link.get("id") or "").strip()
    ]
    videos = await video_repository.list_by_ids(linked_video_ids)
    videos_by_id = {str(video["id"]): video for video in videos}

    items = []
    seen_video_ids: set[str] = set()

    for participant_link in participant_links:
        video_id = str(participant_link.get("video_id") or participant_link.get("id") or "")

        if not video_id or video_id in seen_video_ids:
            continue

        video = videos_by_id.get(video_id)

        if video is None:
            continue

        items.append(_build_video_response(video))
        seen_video_ids.add(video_id)

    items.sort(
        key=lambda item: normalize_utc_datetime(item["created_at"])
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return VideoListResponse(
        items=items,
        total=len(items),
        message="Videos retrieved successfully." if items else "Nenhum vídeo encontrado.",
    )


def _build_video_response(video: dict) -> dict:
    recorded_at = _normalize_datetime_string(
        video.get("recorded_at") or video.get("uploaded_at")
    )

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
    normalized_datetime = normalize_utc_datetime(value)

    if normalized_datetime is None:
        return utc_now().isoformat()

    return normalized_datetime.isoformat()
