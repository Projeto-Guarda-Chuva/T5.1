from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class VideoEmailDispatchRequest(BaseModel):
    reference_date: date | None = None
    video_id: str | None = None


class ParticipantVideoAttachment(BaseModel):
    id: str
    title: str
    recorded_at: datetime
    filename: str
    content_type: str
    size_bytes: int


class VideoEmailDispatchResponse(BaseModel):
    dispatch_id: str
    sent_at: datetime
    participant_id: str
    participant_email: str
    reference_date: date
    delivery_mode: Literal["smtp", "outbox"]
    video: ParticipantVideoAttachment
    message: str


class ParticipantVideoStorageResponse(BaseModel):
    participant_id: str
    video: ParticipantVideoAttachment
    message: str
