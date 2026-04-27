from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    idea_id: Optional[int] = None
    scheduled_publication_id: Optional[int] = None
    platform: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    unread_count: int
