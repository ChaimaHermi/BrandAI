import os
import sys

import pytest

from pathlib import Path

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tests.social_optimizer._social_test_helpers import (
    print_connect_message,
    write_result_json,
)
from tools.social_optimizer.collectors.meta_collector import MetaCollector
from tools.social_publishing.meta_client import MetaGraphError


@pytest.mark.asyncio
async def test_extract_facebook_data():
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    if not token or not page_id:
        await print_connect_message("Facebook", "/api/ai/social/meta/oauth-url")
        pytest.skip("Missing FACEBOOK_PAGE_ACCESS_TOKEN or FACEBOOK_PAGE_ID")

    collector = MetaCollector()
    account_ref = {
        "platform": "facebook",
        "page_access_token": token,
        "facebook_page_id": page_id,
    }

    try:
        posts = await collector.fetch_recent_posts(account_ref, limit=3)
    except MetaGraphError as e:
        await print_connect_message("Facebook", "/api/ai/social/meta/oauth-url")
        pytest.skip(f"Facebook permission/token issue: {e}")

    assert isinstance(posts, list)
    if not posts:
        pytest.skip("No Facebook posts")

    post_id = str(posts[0].get("id") or "").strip()
    if not post_id:
        pytest.skip("Facebook post id not found")

    metrics = await collector.fetch_post_metrics(account_ref, post_id)
    assert isinstance(metrics, dict)

    write_result_json(
        __file__,
        "facebook_result.json",
        {
            "platform": "facebook",
            "posts_count": len(posts),
            "first_post": posts[0],
            "first_post_metrics": metrics,
        },
    )

