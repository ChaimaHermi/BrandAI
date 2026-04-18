from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GeneratedContentCreate(BaseModel):
    platform: Literal["instagram", "facebook", "linkedin"]
    caption: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    char_count: Optional[int] = Field(None, ge=0)


class GeneratedContentPatch(BaseModel):
    status: Optional[Literal["generated", "published", "publish_failed"]] = None
    publish_error: Optional[str] = None


class GeneratedContentOut(BaseModel):
    id: int
    idea_id: int
    platform: str
    caption: str
    image_url: Optional[str] = None
    char_count: Optional[int] = None
    status: str
    published_at: Optional[datetime] = None
    publish_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GeneratedContentListOut(BaseModel):
    items: list[GeneratedContentOut]
    total: int
