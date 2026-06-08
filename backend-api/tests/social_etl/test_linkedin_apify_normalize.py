from app.social_etl.extraction.linkedin_apify_normalize import (
    extract_linkedin_profile_counters,
    flatten_apify_items,
    normalize_linkedin_apify_items,
    post_id_from_url,
    resolve_post_external_id,
)


def test_post_id_from_activity_url():
    url = "https://www.linkedin.com/posts/activity-7449813611339882496-PnsY"
    assert post_id_from_url(url) == "7449813611339882496"


def test_normalize_skips_profile_and_keeps_posts():
    items = [
        {
            "profileUrl": "https://www.linkedin.com/in/chaima-hermi/",
            "connections": 512,
            "followers": 100059,
        },
        {
            "text": "Post A",
            "postedAt": "2026-04-14T10:00:00.000Z",
            "numLikes": 4,
            "postUrl": "https://www.linkedin.com/posts/activity-111-PnsY",
        },
        {
            "text": "Post B",
            "postedAt": "2026-03-01T10:00:00.000Z",
            "numLikes": 2,
            "postUrl": "https://www.linkedin.com/posts/activity-222-PnsY",
        },
    ]
    posts = normalize_linkedin_apify_items(items, limit=10)
    assert len(posts) == 2
    assert posts[0]["id"] == "111"
    assert posts[0]["likes"] == 4


def test_flatten_nested_posts_array():
    items = [
        {
            "profileUrl": "https://www.linkedin.com/in/demo/",
            "posts": [
                {
                    "text": "Nested",
                    "numLikes": 1,
                    "postUrl": "https://www.linkedin.com/posts/activity-333-PnsY",
                }
            ],
        }
    ]
    flat = flatten_apify_items(items)
    posts = normalize_linkedin_apify_items(flat, limit=10)
    assert len(posts) == 1
    assert posts[0]["id"] == "333"


def test_profile_counters_prefer_connections_for_personal_profile():
    items = [
        {
            "profileUrl": "https://www.linkedin.com/in/chaima-hermi/",
            "connections": 512,
            "followers": 100059,
        }
    ]
    counters = extract_linkedin_profile_counters(
        items,
        profile_url="https://www.linkedin.com/in/chaima-hermi/",
    )
    assert counters["followers_count"] == 512
    assert counters["connections_count"] == 512


def test_resolve_post_external_id_without_explicit_id():
    item = {
        "text": "Hello",
        "postUrl": "https://www.linkedin.com/posts/activity-999-test",
    }
    assert resolve_post_external_id(item) == "999"
