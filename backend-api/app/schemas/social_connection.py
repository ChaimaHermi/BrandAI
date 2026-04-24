from __future__ import annotations

from pydantic import BaseModel, Field


class MetaPageIn(BaseModel):
    id: str | int = Field(..., description="Page Facebook id")
    name: str | None = None
    access_token: str = Field(..., min_length=1)


class MetaConnectionUpsert(BaseModel):
    user_access_token: str = Field(..., min_length=1)
    pages: list[MetaPageIn] = Field(..., min_length=1)
    selected_page_id: str | None = None


class MetaSelectedPagePatch(BaseModel):
    selected_page_id: str = Field(..., min_length=1)


class LinkedInConnectionUpsert(BaseModel):
    access_token: str = Field(..., min_length=1)
    person_urn: str = Field(..., min_length=1)
    name: str | None = None


class MetaPageOut(BaseModel):
    id: str
    name: str | None = None
    access_token: str


class MetaConnectionOut(BaseModel):
    user_access_token: str
    pages: list[MetaPageOut]
    selected_page_id: str | None = None


class LinkedInConnectionOut(BaseModel):
    access_token: str
    person_urn: str
    name: str | None = None


class SocialConnectionsOut(BaseModel):
    meta: MetaConnectionOut | None = None
    linkedin: LinkedInConnectionOut | None = None
