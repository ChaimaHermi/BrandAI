"""Schémas API pour naming / slogan / palette / logo / brand_kit."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NamingResultOut(BaseModel):
    id: UUID
    idea_id: int
    status: str
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen_name: Optional[str] = None
    chosen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NamingResultPatch(BaseModel):
    """Champs optionnels : seuls les champs fournis sont mis à jour."""

    status: Optional[str] = None
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen_name: Optional[str] = None
    chosen_at: Optional[datetime] = None


class SloganResultOut(BaseModel):
    id: UUID
    idea_id: int
    status: str
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen_slogan: Optional[str] = None
    based_on_name: Optional[str] = None
    chosen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SloganResultPatch(BaseModel):
    status: Optional[str] = None
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen_slogan: Optional[str] = None
    based_on_name: Optional[str] = None
    chosen_at: Optional[datetime] = None


class PaletteResultOut(BaseModel):
    id: UUID
    idea_id: int
    status: str
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen: Optional[Any] = None
    chosen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaletteResultPatch(BaseModel):
    status: Optional[str] = None
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    chosen: Optional[Any] = None
    chosen_at: Optional[datetime] = None


class LogoResultOut(BaseModel):
    id: UUID
    idea_id: int
    status: str
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    style: Optional[str] = None
    logo_type: Optional[str] = None
    svg_data: Optional[str] = None
    variants: Optional[Any] = None
    chosen: Optional[Any] = None
    chosen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogoResultPatch(BaseModel):
    status: Optional[str] = None
    preferences: Optional[Any] = None
    generated: Optional[Any] = None
    style: Optional[str] = None
    logo_type: Optional[str] = None
    svg_data: Optional[str] = None
    variants: Optional[Any] = None
    chosen: Optional[Any] = None
    chosen_at: Optional[datetime] = None


class BrandKitOut(BaseModel):
    id: UUID
    idea_id: int
    naming_id: Optional[UUID] = None
    slogan_id: Optional[UUID] = None
    palette_id: Optional[UUID] = None
    logo_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandKitPatch(BaseModel):
    naming_id: Optional[UUID] = None
    slogan_id: Optional[UUID] = None
    palette_id: Optional[UUID] = None
    logo_id: Optional[UUID] = None
