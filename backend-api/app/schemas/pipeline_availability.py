"""Indicateurs de présence de résultats pipeline (sans 404)."""

from pydantic import BaseModel


class PipelineAvailabilityOut(BaseModel):
    has_market_analysis: bool
    has_marketing_plan: bool
    has_branding_naming: bool
