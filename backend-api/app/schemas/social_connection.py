from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MetaPageIn(BaseModel):
    id: str | int = Field(..., description="Page Facebook id")
    name: str | None = None
    access_token: str = Field(..., min_length=1)


class MetaConnectionUpsert(BaseModel):
    user_access_token: str = Field(..., min_length=1)
    pages: list[MetaPageIn] = Field(..., min_length=1)
    selected_page_id: str | None = None
    token_expires_at: datetime | None = Field(
        None,
        description="Expiration du jeton utilisateur Meta si connue (OAuth).",
    )


class MetaSelectedPagePatch(BaseModel):
    selected_page_id: str = Field(..., min_length=1)


class LinkedInProfileUrlPatch(BaseModel):
    """URL de profil LinkedIn optionnelle (ex. pour l’agent Optimizer)."""

    profile_url: str | None = Field(
        None,
        max_length=2048,
        description="https://www.linkedin.com/in/… — laisser vide pour effacer.",
    )

    @field_validator("profile_url", mode="before")
    @classmethod
    def normalize_optional_url(cls, v: object) -> str | None:
        if v is None:
            return None
        if not isinstance(v, str):
            return None
        s = v.strip()
        if not s:
            return None
        low = s.lower()
        if not low.startswith(("http://", "https://")):
            s = f"https://{s.lstrip('/')}"
        elif low.startswith("http://"):
            s = "https://" + s[7:]
        return s

    @field_validator("profile_url")
    @classmethod
    def must_be_https_linkedin(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s.startswith("https://"):
            raise ValueError("L’URL doit utiliser HTTPS (https://…).")
        if "linkedin.com" not in s.lower():
            raise ValueError("L’URL doit appartenir au domaine linkedin.com (ex. /in/… ou /company/…).")
        return s


class LinkedInConnectionUpsert(BaseModel):
    access_token: str = Field(..., min_length=1)
    person_urn: str = Field(..., min_length=1)
    name: str | None = None
    token_expires_at: datetime | None = None


class MetaPageOut(BaseModel):
    id: str
    name: str | None = None
    access_token: str


class InstagramBusinessConnectionOut(BaseModel):
    platform_account_id: str | None = None
    profile_url: str | None = None
    account_name: str | None = None
    page_name: str | None = None
    token_expires_at: datetime | None = None


class MetaConnectionOut(BaseModel):
    user_access_token: str
    pages: list[MetaPageOut]
    selected_page_id: str | None = None
    account_name: str | None = None
    page_name: str | None = None
    profile_url: str | None = None
    token_expires_at: datetime | None = None
    instagram_business: InstagramBusinessConnectionOut | None = None


class LinkedInConnectionOut(BaseModel):
    access_token: str
    person_urn: str
    name: str | None = None
    account_name: str | None = None
    page_name: str | None = None
    profile_url: str | None = None
    token_expires_at: datetime | None = None


class SocialConnectionsOut(BaseModel):
    meta: MetaConnectionOut | None = None
    linkedin: LinkedInConnectionOut | None = None
