from datetime import datetime
from typing import Any

from pydantic import BaseModel

class ConfigurationSummary(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ConfigurationDetail(ConfigurationSummary):
    parameters: dict[str, Any]

class ConfigurationListResponse(BaseModel):
    items: list[ConfigurationSummary]
    total: int
    message: str
