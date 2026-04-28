from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WebsiteProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    idea_id: int
    status: str
    description_json: dict[str, Any] | None = None
    current_html: str | None = None
    current_version: int
    conversation_json: list[dict[str, Any]]
    approved: bool
    approved_at: datetime | None = None
    last_deployment_id: str | None = None
    last_deployment_url: str | None = None
    last_deployment_state: str | None = None
    created_at: datetime
    updated_at: datetime


class WebsiteProjectPatch(BaseModel):
    status: str | None = Field(None, max_length=30)
    description_json: dict[str, Any] | None = None
    current_html: str | None = None
    current_version: int | None = Field(None, ge=1)
    conversation_json: list[dict[str, Any]] | None = None
    approved: bool | None = None
    approved_at: datetime | None = None
    last_deployment_id: str | None = None
    last_deployment_url: str | None = None
    last_deployment_state: str | None = None


class WebsiteMessageIn(BaseModel):
    id: str | None = None
    role: str = Field(..., min_length=1, max_length=30)
    type: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)
    meta: dict[str, Any] | None = None
    created_at: datetime | None = None


class WebsiteApproveOut(BaseModel):
    success: bool
    idea_id: int
    approved: bool
    approved_at: datetime

