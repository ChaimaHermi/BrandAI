from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class BrandIdentityCreate(BaseModel):
    status: str = "done"
    result_json: Optional[Any] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BrandIdentityOut(BaseModel):
    id: int
    idea_id: int
    status: str
    result_json: Optional[Any] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
