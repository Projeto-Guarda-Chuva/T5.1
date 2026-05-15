from app.config import settings
from app.database import db


async def seed_participant_video_email_data() -> None:
    await db["participant_videos"].create_index("participant_id")
    await db["participant_videos"].create_index("recorded_at")
    await db["video_email_dispatch_logs"].create_index("participant_id")
    await db["email_outbox"].create_index("participant_id")
    await db[f"{settings.VIDEO_GRIDFS_BUCKET_NAME}.files"].create_index(
        "metadata.binding_key",
        sparse=True,
    )
