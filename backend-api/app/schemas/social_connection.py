from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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


class LinkedInUrlPatch(BaseModel):
    """URL de profil LinkedIn optionnelle (saisie manuelle, ex. pour l’agent Optimizer)."""

    linkedin_url: str | None = Field(
        None,
        max_length=2048,
        description="https://www.linkedin.com/in/… — laisser vide pour effacer.",
    )

    @field_validator("linkedin_url", mode="before")
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

    @field_validator("linkedin_url")
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


class MetaPageOut(BaseModel):
    id: str
    name: str | None = None
    access_token: str


class MetaConnectionOut(BaseModel):
    user_access_token: str
    pages: list[MetaPageOut]
    selected_page_id: str | None = None
    account_name: str | None = None
    page_name: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None


class LinkedInConnectionOut(BaseModel):
    access_token: str
    person_urn: str
    name: str | None = None
    account_name: str | None = None
    page_name: str | None = None
    linkedin_url: str | None = None


class SocialConnectionsOut(BaseModel):
    meta: MetaConnectionOut | None = None
    linkedin: LinkedInConnectionOut | None = None
