from pydantic import BaseModel
from typing import List, Optional

class VideoResponse(BaseModel):
    id: str
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