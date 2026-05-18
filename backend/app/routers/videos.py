from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies import get_current_user
from app.repositories.email_outbox_repository import EmailOutboxRepository
from app.repositories.participant_recording_event_repository import ParticipantRecordingEventRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.repositories.video_email_dispatch_repository import VideoEmailDispatchRepository
from app.repositories.video_file_repository import VideoFileRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoListResponse, VideoUploadResponse
from app.services import video_service
from app.services.video_email_sender import VideoEmailSender
from app.services.video_upload_service import VideoUploadInvalidError, VideoUploadService

router = APIRouter(prefix="/videos", tags=["Videos"])

video_upload_service = VideoUploadService(
    video_repository=VideoRepository(),
    video_file_repository=VideoFileRepository(),
    participant_recording_event_repository=ParticipantRecordingEventRepository(),
    participant_video_repository=ParticipantVideoRepository(),
    participant_repository=ParticipantRepository(),
    dispatch_repository=VideoEmailDispatchRepository(),
    email_sender=VideoEmailSender(EmailOutboxRepository()),
)


@router.get("", response_model=VideoListResponse)
async def get_videos(email: str = Depends(get_current_user)):
    return await video_service.list_user_videos(email)


@router.post("", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    video: UploadFile = File(...),
    title: str | None = Form(None),
    recorded_at: datetime | None = Form(None),
) -> VideoUploadResponse:
    try:
        return await video_upload_service.upload_video(
            filename=video.filename or "video.mp4",
            content_type=video.content_type,
            file_bytes=await video.read(),
            title=title,
            recorded_at=recorded_at,
            uploaded_by_email="admin@t51.com",
        )
    except VideoUploadInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await video.close()


@router.get("/meus-videos", response_model=VideoListResponse, include_in_schema=False)
async def get_meus_videos(email: str = Depends(get_current_user)):
    return await video_service.list_user_videos(email)