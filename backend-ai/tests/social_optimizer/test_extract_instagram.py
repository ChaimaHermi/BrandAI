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
async def test_extract_instagram_data():
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    ig_user_id = os.getenv("INSTAGRAM_IG_USER_ID")
    if not token or not ig_user_id:
        await print_connect_message("Instagram/Meta", "/api/ai/social/meta/oauth-url")
        pytest.skip("Missing FACEBOOK_PAGE_ACCESS_TOKEN or INSTAGRAM_IG_USER_ID")

    collector = MetaCollector()
    account_ref = {
        "platform": "instagram",
        "page_access_token": token,
        "ig_user_id": ig_user_id,
    }

    try:
        posts = await collector.fetch_recent_posts(account_ref, limit=3)
    except MetaGraphError as e:
        await print_connect_message("Instagram/Meta", "/api/ai/social/meta/oauth-url")
        pytest.skip(f"Instagram permission/token issue: {e}")

    assert isinstance(posts, list)
    if not posts:
        pytest.skip("No Instagram posts")

    post_id = str(posts[0].get("id") or "").strip()
    if not post_id:
        pytest.skip("Instagram post id not found")

    metrics = await collector.fetch_post_metrics(account_ref, post_id)
    assert isinstance(metrics, dict)

    write_result_json(
        __file__,
        "instagram_result.json",
        {
            "platform": "instagram",
            "posts_count": len(posts),
            "first_post": posts[0],
            "first_post_metrics": metrics,
        },
    )

