import json
from pathlib import Path

from app.config import settings
from app.database import db
from app.repositories.email_outbox_repository import EmailOutboxRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.repositories.video_file_repository import VideoFileRepository
from app.repositories.video_email_dispatch_repository import (
    VideoEmailDispatchRepository,
)


_DATA_DIR = Path(__file__).resolve().parent / "data"


async def seed_participant_video_email_data() -> None:
    participant_video_repository = ParticipantVideoRepository()

    await _seed_collection_if_empty(
        repository=ParticipantRepository(),
        file_name="participants.json",
    )
    await _seed_collection_if_empty(
        repository=participant_video_repository,
        file_name="participant_videos.json",
    )
    await _seed_collection_if_empty(
        repository=VideoEmailDispatchRepository(),
        file_name="video_email_dispatch_logs.json",
    )
    await _seed_collection_if_empty(
        repository=EmailOutboxRepository(),
        file_name="email_outbox.json",
    )

    await _ensure_seed_video_file(participant_video_repository)

    await db["participant_videos"].create_index("participant_id")
    await db["participant_videos"].create_index("recorded_at")
    await db["video_email_dispatch_logs"].create_index("participant_id")
    await db["email_outbox"].create_index("participant_id")
    await db[f"{settings.VIDEO_GRIDFS_BUCKET_NAME}.files"].create_index(
        "metadata.source_path",
        unique=True,
        sparse=True,
    )
    await db[f"{settings.VIDEO_GRIDFS_BUCKET_NAME}.files"].create_index(
        "metadata.binding_key",
        sparse=True,
    )


async def _seed_collection_if_empty(repository, file_name: str) -> None:
    if await repository.exists_any():
        return

    file_path = _DATA_DIR / file_name

    if not file_path.exists():
        return

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"The seed file {file_name} must contain a list.")

    await repository.insert_many(data)


async def _ensure_seed_video_file(participant_video_repository: ParticipantVideoRepository) -> None:
    if not settings.VIDEO_SEED_FILE_PATH or not settings.VIDEO_SEED_TARGET_VIDEO_ID:
        return

    source_path = Path(settings.VIDEO_SEED_FILE_PATH).expanduser()

    if not source_path.exists():
        return

    file_data = await VideoFileRepository().ensure_file_from_path(source_path)
    video_id = settings.VIDEO_SEED_TARGET_VIDEO_ID
    video_cursor = db["participant_videos"].find(
        {"id": video_id},
        {"_id": 0, "participant_id": 1},
    )
    matching_videos = await video_cursor.to_list(length=2)

    if len(matching_videos) != 1:
        return

    await participant_video_repository.attach_file_to_video(
        matching_videos[0]["participant_id"],
        video_id,
        file_data,
    )
