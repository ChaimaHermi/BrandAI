from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KpiBlock(BaseModel):
    followers: int | None = None
    engagement_rate: float | None = None
    reach: int | None = None
    post_count: int | None = None


class EvolutionPoint(BaseModel):
    date: str
    value: float


class TopPostOut(BaseModel):
    id: str
    preview: str | None = None
    platform: str
    likes: int | None = None
    comments: int | None = None
    reach: int | None = None
    published_at: str | None = None


class PlatformStatsOut(BaseModel):
    kpis: KpiBlock
    evolution: list[EvolutionPoint] = Field(default_factory=list)
    top_posts: list[TopPostOut] = Field(default_factory=list)


class SocialEtlSyncOut(BaseModel):
    output_dir: str
    runs: list[dict[str, Any]]
    warnings: list[str] = Field(default_factory=list)


class OptimizerConnectionsSummaryOut(BaseModel):
    """État des connexions pour l’idée (sans jetons sensibles)."""

    has_meta_facebook: bool = False
    has_instagram: bool = False
    has_linkedin: bool = False
    linkedin_profile_url: str | None = None
    facebook_page_label: str | None = None
    instagram_label: str | None = None
    can_run_social_etl: bool = False
    blockers: list[str] = Field(default_factory=list)
