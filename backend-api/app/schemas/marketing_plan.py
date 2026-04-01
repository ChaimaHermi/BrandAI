from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class MarketingPlanCreate(BaseModel):
    result_json: Optional[Any] = None
    status: Optional[str] = None


class MarketingPlanOut(BaseModel):
    id: int
    idea_id: Optional[int] = None
    result_json: Optional[Any] = None
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarketingPlanListOut(BaseModel):
    items: list[MarketingPlanOut]
    total: int
