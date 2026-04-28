from __future__ import annotations

from tools.website_builder.brand_context_fetch import BrandContext, fetch_full_brand_context


class WebsiteContextTool:
    """Phase 1: load and normalize project + brand context."""

    async def fetch(self, *, idea_id: int, access_token: str) -> BrandContext:
        return await fetch_full_brand_context(idea_id, access_token)

