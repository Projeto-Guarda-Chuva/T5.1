from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class ConfigurationSummary(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ConfigurationDetail(ConfigurationSummary):
    parameters: dict[str, Any]

class ConfigurationCreateParameters(BaseModel):
    movement_speed: float = Field(..., gt=0)
    movement_duration_seconds: int = Field(..., gt=0)
    video_capture_enabled: bool
    audio_capture_enabled: bool

class ConfigurationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    parameters: ConfigurationCreateParameters

class ConfigurationListResponse(BaseModel):
    items: list[ConfigurationSummary]
    total: int
    message: str
