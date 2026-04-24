import os
import sys

import httpx
import pytest

from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tests.social_optimizer._social_test_helpers import (
    print_connect_message,
    write_result_json,
)
from tools.social_optimizer.collectors.linkedin_collector import LinkedInCollector


@pytest.mark.asyncio
async def test_extract_linkedin_data():
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")
    if not token or not person_urn:
        await print_connect_message("LinkedIn", "/api/ai/social/linkedin/oauth-url")
        pytest.skip("Missing LINKEDIN_ACCESS_TOKEN or LINKEDIN_PERSON_URN")

    collector = LinkedInCollector()
    account_ref = {
        "access_token": token,
        "author_urn": person_urn,
    }

    try:
        posts = await collector.fetch_recent_posts(account_ref, limit=3)
    except httpx.HTTPStatusError as e:
        await print_connect_message("LinkedIn", "/api/ai/social/linkedin/oauth-url")
        pytest.skip(f"LinkedIn permission/token issue: HTTP {e.response.status_code}")

    assert isinstance(posts, list)
    if not posts:
        pytest.skip("No LinkedIn posts")

    post_id = str(posts[0].get("id") or "").strip()
    if not post_id:
        pytest.skip("LinkedIn post id not found")

    try:
        metrics = await collector.fetch_post_metrics(account_ref, post_id)
    except httpx.HTTPStatusError as e:
        await print_connect_message("LinkedIn", "/api/ai/social/linkedin/oauth-url")
        pytest.skip(f"LinkedIn metrics permission issue: HTTP {e.response.status_code}")

    assert isinstance(metrics, dict)

    write_result_json(
        __file__,
        "linkedin_result.json",
        {
            "platform": "linkedin",
            "posts_count": len(posts),
            "first_post": posts[0],
            "first_post_metrics": metrics,
        },
    )

