from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ScheduledPublicationCreate(BaseModel):
    generated_content_id: int = Field(..., ge=1)
    scheduled_at: datetime = Field(..., description="UTC instant for publication")
    timezone: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class ScheduledPublicationPatch(BaseModel):
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=64)
    title: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Optional[Literal["scheduled", "cancelled"]] = None
    caption_snapshot: Optional[str] = Field(None, min_length=1)
    image_url_snapshot: Optional[str] = None


class ScheduledPublicationOut(BaseModel):
    id: int
    user_id: int
    idea_id: int
    generated_content_id: int
    platform: str
    caption_snapshot: str
    image_url_snapshot: Optional[str] = None
    scheduled_at: datetime
    timezone: Optional[str] = None
    status: str
    attempt_count: int
    last_error: Optional[str] = None
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduledPublicationListOut(BaseModel):
    items: list[ScheduledPublicationOut]
    total: int
