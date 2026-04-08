"""Persistence clients for backend-api, grouped by domain."""

from app.services.persistence.branding_persistence_service import (
    fetch_branding_merged_generated,
    persist_brand_identity_row,
    persist_branding_results_tables,
)
from app.services.persistence.market_marketing_persistence_service import (
    persist_market_result,
    persist_marketing_result,
)

__all__ = [
    "persist_market_result",
    "persist_marketing_result",
    "fetch_branding_merged_generated",
    "persist_brand_identity_row",
    "persist_branding_results_tables",
]
