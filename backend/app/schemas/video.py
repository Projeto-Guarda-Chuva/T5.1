from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

class VideoResponse(BaseModel):
    id: str
    participant_video_id: Optional[str] = None
    title: str
    created_at: str
    duration_seconds: int
    thumbnail_url: str
    video_url: str
    status: str

class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    message: str

class VideoClaimRequest(BaseModel):
    participation_time: str

class VideoClaimResponse(VideoResponse):
    message: str


class VideoUploadResponse(BaseModel):
    id: str
    title: str
    recorded_at: datetime
    uploaded_at: datetime
    filename: str
    content_type: str
    size_bytes: int
    associated_participant_ids: List[str]
    associated_participants_count: int
    message: str
