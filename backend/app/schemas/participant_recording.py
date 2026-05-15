from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ParticipationEventResponse(BaseModel):
    participant_id: str
    participant_email: str
    event_type: Literal["will_participate", "already_participated"]
    recorded_at: datetime
    associated_video_ids: list[str] = []
    associated_videos_count: int = 0
    message: str
