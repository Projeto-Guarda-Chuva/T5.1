from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("name", "description")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("must contain at least 1 character")

        return normalized_value


class ConfigurationListResponse(BaseModel):
    items: list[ConfigurationSummary]
    total: int
    message: str


class ConfigurationSelectionResponse(BaseModel):
    configuration: ConfigurationDetail
    message: str


class EffectiveConfigurationResponse(BaseModel):
    configuration: ConfigurationDetail | None
    source: Literal["active", "default", "none"]
    has_active_configuration: bool
    message: str
