from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OperationLogEntry(BaseModel):
    id: str
    occurred_at: datetime
    duration_seconds: int = Field(..., ge=0)
    participant_email: str
    status: Literal["success", "error"]
    status_text: str
    description: str


class OperationLogListResponse(BaseModel):
    items: list[OperationLogEntry]
    total: int
    message: str
