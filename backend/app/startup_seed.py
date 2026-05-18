from app.config import settings
from app.database import db
from app.time_utils import normalize_utc_datetime, utc_now


async def seed_participant_video_email_data() -> None:
    await _migrate_legacy_participant_videos()
    await _deduplicate_participant_video_links()
    await db["videos"].create_index("id", unique=True)
    await db["videos"].create_index("uploaded_at")
    await db["videos"].create_index("recorded_at")
    await db["participant_videos"].create_index("participant_id")
    await db["participant_videos"].create_index("video_id")
    await db["participant_videos"].create_index(
        [("participant_id", 1), ("video_id", 1)],
        unique=True,
        name="participant_video_unique_link",
    )
    await db["participant_recording_events"].create_index("participant_id")
    await db["participant_recording_events"].create_index(
        [("event_type", 1), ("created_at", 1)],
        name="participant_recording_event_window",
    )
    await db["video_email_dispatch_logs"].create_index("participant_id")
    await db["email_outbox"].create_index("participant_id")
    await _ensure_gridfs_binding_key_index()


async def _migrate_legacy_participant_videos() -> None:
    legacy_cursor = db["participant_videos"].find(
        {"video_id": {"$exists": False}},
        {"_id": 0},
    )
    legacy_records = await legacy_cursor.to_list(length=None)

    for legacy_record in legacy_records:
        participant_id = str(legacy_record.get("participant_id", "")).strip()
        video_id = str(legacy_record.get("id", "")).strip()

        if not participant_id or not video_id:
            continue

        recorded_at = normalize_utc_datetime(legacy_record.get("recorded_at")) or utc_now()
        uploaded_at = normalize_utc_datetime(legacy_record.get("uploaded_at")) or recorded_at

        await db["videos"].update_one(
            {"id": video_id},
            {
                "$setOnInsert": {
                    "id": video_id,
                    "title": legacy_record.get("title", "Vídeo da participação"),
                    "status": legacy_record.get("status", "available"),
                    "recorded_at": recorded_at,
                    "uploaded_at": uploaded_at,
                    "duration_seconds": int(legacy_record.get("duration_seconds", 0) or 0),
                    "thumbnail_url": str(legacy_record.get("thumbnail_url", "") or ""),
                    "file_id": legacy_record.get("file_id"),
                    "filename": legacy_record.get("filename"),
                    "content_type": legacy_record.get("content_type"),
                    "size_bytes": int(legacy_record.get("size_bytes", 0) or 0),
                }
            },
            upsert=True,
        )
        await db["participant_videos"].update_one(
            {"participant_id": participant_id, "id": video_id},
            {
                "$set": {
                    "video_id": video_id,
                    "associated_at": normalize_utc_datetime(
                        legacy_record.get("associated_at")
                    )
                    or recorded_at,
                    "association_source": legacy_record.get("association_source")
                    or "legacy_migration",
                }
            },
        )


async def _deduplicate_participant_video_links() -> None:
    pipeline = [
        {
            "$group": {
                "_id": {
                    "participant_id": "$participant_id",
                    "video_id": {"$ifNull": ["$video_id", "$id"]},
                },
                "document_ids": {"$push": "$_id"},
                "count": {"$sum": 1},
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = await db["participant_videos"].aggregate(pipeline).to_list(length=None)

    for duplicate_group in duplicates:
        document_ids = duplicate_group.get("document_ids", [])

        for redundant_document_id in document_ids[1:]:
            await db["participant_videos"].delete_one({"_id": redundant_document_id})


async def _ensure_gridfs_binding_key_index() -> None:
    files_collection = db[f"{settings.VIDEO_GRIDFS_BUCKET_NAME}.files"]
    existing_indexes = await files_collection.index_information()

    for index_definition in existing_indexes.values():
        keys = index_definition.get("key", [])
        normalized_keys = list(keys)

        if normalized_keys != [("metadata.binding_key", 1)]:
            continue

        # Base já possui um índice para binding_key. Se ele não for unique,
        # não tentamos recriá-lo com opções diferentes para evitar falha no startup.
        return

    await files_collection.create_index(
        "metadata.binding_key",
        sparse=True,
        unique=True,
        name="gridfs_binding_key_unique",
    )
