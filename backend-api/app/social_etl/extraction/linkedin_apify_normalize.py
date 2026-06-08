"""
Post-traitement des items renvoyés par un acteur Apify LinkedIn (profil / posts).

Logique pure, sans HTTP ni OAuth — utilisé par ``linkedin_extractor``.
"""

from __future__ import annotations

import re
from typing import Any

_ACTIVITY_ID_RE = re.compile(
    r"(?:activity[-:](\d+)|urn:li:activity:(\d+)|/feed/update/urn:li:activity:(\d+))",
    re.IGNORECASE,
)


def _linkedin_comments_count_and_list(item: dict[str, Any]) -> tuple[int, list | None]:
    """
    Apify peut envoyer ``comments`` comme liste (souvent vide) : ne pas utiliser ``or``
    pour retomber sur ``numComments``, sinon on perd le vrai total.
    """
    raw = item.get("comments")
    num_raw = item.get("numComments")
    parsed_num: int | None = None
    if isinstance(num_raw, (int, float)) and not isinstance(num_raw, bool):
        parsed_num = int(num_raw)
    elif isinstance(num_raw, str) and num_raw.strip().isdigit():
        parsed_num = int(num_raw.strip())

    if isinstance(raw, list):
        if raw:
            return len(raw), raw
        return (parsed_num if parsed_num is not None else 0), None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return int(raw), None
    if parsed_num is not None:
        return parsed_num, None
    return 0, None


def parse_count_like(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return None

    raw = value.strip().lower().replace(",", "").replace(" ", "")
    if not raw:
        return None
    m = re.match(r"^\+?(\d+(?:\.\d+)?)([km]?)$", raw)
    if not m:
        return None
    num = float(m.group(1))
    suffix = m.group(2)
    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000
    return int(num)


def _first_str(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def post_id_from_url(url: str | None) -> str | None:
    """Extrait l'identifiant d'activité LinkedIn depuis une URL de post."""
    if not url or not isinstance(url, str):
        return None
    m = _ACTIVITY_ID_RE.search(url)
    if not m:
        return None
    for group in m.groups():
        if group:
            return group
    return None


def resolve_post_external_id(item: dict[str, Any], post_url: str | None = None) -> str | None:
    for key in ("id", "postId", "activityId", "urn", "entityUrn"):
        raw = item.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        from_url = post_id_from_url(text)
        if from_url:
            return from_url
        m = re.search(r"(\d{8,})", text)
        if m:
            return m.group(1)
        if key in {"id", "postId", "activityId"} and text.isdigit():
            return text
    url = post_url or _post_url_from_item(item)
    return post_id_from_url(url)


def _post_url_from_item(item: dict[str, Any]) -> str | None:
    return _first_str(
        item.get("postUrl"),
        item.get("url"),
        item.get("activityUrl"),
        item.get("linkedinUrl"),
        item.get("postLink"),
        item.get("shareUrl"),
    )


def _is_profile_only_item(item: dict[str, Any]) -> bool:
    """Item profil sans signal de publication."""
    url = _first_str(item.get("profileUrl"), item.get("url"), item.get("linkedinUrl")) or ""
    low_url = url.lower()
    if low_url and "/in/" in low_url and "activity-" not in low_url and "/posts/" not in low_url:
        has_post_text = bool(
            _first_str(item.get("text"), item.get("content"), item.get("postText"))
        )
        has_post_date = bool(
            item.get("postedAt") or item.get("timestamp") or item.get("date")
        )
        if not has_post_text and not has_post_date:
            return True

    raw_type = str(item.get("type") or item.get("entityType") or "").strip().lower()
    if raw_type in {"profile", "person", "company", "header"}:
        return True
    return False


def _is_likely_post_item(item: dict[str, Any]) -> bool:
    if not isinstance(item, dict) or not item:
        return False
    if _is_profile_only_item(item):
        return False

    url = _post_url_from_item(item) or ""
    low_url = url.lower()
    if "activity-" in low_url or "/posts/" in low_url or "feed/update" in low_url:
        return True

    if resolve_post_external_id(item, url):
        return True

    has_text = bool(_first_str(item.get("text"), item.get("content"), item.get("postText")))
    has_date = bool(item.get("postedAt") or item.get("timestamp") or item.get("date"))
    has_engagement = any(
        item.get(k) is not None
        for k in ("likes", "numLikes", "comments", "numComments", "reposts", "numShares", "shares")
    )
    raw_type = str(item.get("type") or "").strip().lower()
    if "post" in raw_type or "share" in raw_type or "activity" in raw_type:
        return True
    return has_text and (has_date or has_engagement)


def flatten_apify_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aplatit les tableaux ``posts`` / ``updates`` imbriqués renvoyés par certains acteurs."""
    flat: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        nested_keys = ("posts", "updates", "activities", "recentPosts", "elements")
        expanded = False
        for key in nested_keys:
            nested = item.get(key)
            if isinstance(nested, list) and nested:
                for sub in nested:
                    if isinstance(sub, dict):
                        flat.append(sub)
                expanded = True
                break
        if not expanded:
            flat.append(item)
    return flat


def _linkedin_post_type_api(item: dict[str, Any]) -> str:
    """
    Normalise le type de post LinkedIn en catégories simples exploitables:
    image | video | text | document | link | carousel | post | unknown
    """
    raw_type = str(item.get("type") or "").strip().lower()

    if "video" in raw_type:
        return "video"
    if "image" in raw_type or "photo" in raw_type:
        return "image"
    if "document" in raw_type or "pdf" in raw_type:
        return "document"
    if "carousel" in raw_type or "album" in raw_type:
        return "carousel"
    if "link" in raw_type or "article" in raw_type:
        return "link"
    if raw_type in {"text", "textpost", "post_text"}:
        return "text"

    image_keys = ("images", "image", "imageUrl", "image_url", "media", "mediaUrl", "media_url")
    for key in image_keys:
        val = item.get(key)
        if isinstance(val, list) and len(val) > 0:
            return "image"
        if isinstance(val, dict) and val:
            return "image"
        if isinstance(val, str) and val.strip():
            return "image"

    text_value = item.get("text") or item.get("content") or item.get("postText")
    if isinstance(text_value, str) and text_value.strip():
        return "text"

    if raw_type:
        return raw_type
    return "unknown"


def _metric_int(item: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        raw = item.get(key)
        if raw is None or isinstance(raw, bool):
            continue
        if isinstance(raw, (int, float)):
            return int(raw)
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
    return None


def normalize_linkedin_apify_items(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Aligne les posts Apify sur le schéma historique ``linkedin_extract_result.json``."""
    posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    flat_items = flatten_apify_items(items)

    for item in flat_items:
        if len(posts) >= limit:
            break
        if not _is_likely_post_item(item):
            continue

        post_url = _post_url_from_item(item)
        pid = resolve_post_external_id(item, post_url)
        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)

        post_type_api = _linkedin_post_type_api(item)
        comments_count, comments_list = _linkedin_comments_count_and_list(item)
        likes = _metric_int(item, "likes", "numLikes", "likeCount", "reactions")
        reposts = _metric_int(item, "reposts", "numShares", "shares", "shareCount")

        row: dict[str, Any] = {
            "id": pid,
            "post_type_api": post_type_api,
            "text": item.get("text") or item.get("content") or item.get("postText"),
            "published_at": item.get("postedAt") or item.get("timestamp") or item.get("date"),
            "post_url": post_url,
            "likes": likes if likes is not None else 0,
            "comments": comments_count,
            "reposts": reposts if reposts is not None else 0,
            "raw": item,
        }
        if comments_list:
            row["comments_list"] = comments_list
        posts.append(row)
    return posts


def _profile_scan_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Limite l'extraction des compteurs aux items profil (évite le bruit des posts)."""
    profile_items = [i for i in items if isinstance(i, dict) and _is_profile_only_item(i)]
    return profile_items if profile_items else items[:1]


def _pick_network_size(
    followers: int | None,
    connections: int | None,
    *,
    profile_url: str | None = None,
) -> int | None:
    """
    Pour un profil /in/ personnel, LinkedIn expose surtout des relations.
    On préfère ``connections`` si ``followers`` est absent ou manifestement aberrant.
    """
    is_personal = bool(profile_url and "/in/" in profile_url.lower())

    if connections is not None and connections > 0:
        if followers is None or followers <= 0:
            return connections
        if is_personal and followers > max(connections * 3, 10_000):
            return connections
        if followers > 500_000:
            return connections

    return followers if followers is not None and followers > 0 else connections


def extract_linkedin_profile_counters(
    items: list[dict[str, Any]],
    *,
    profile_url: str | None = None,
) -> dict[str, Any]:
    """Déduit followers / connexions / nombre de posts depuis le payload Apify."""
    scan_items = _profile_scan_items(flatten_apify_items(items))

    followers_keys = {
        "followers",
        "followersCount",
        "followerCount",
        "numFollowers",
        "subscriberCount",
        "subscribers",
    }
    connections_keys = {
        "connections",
        "connectionsCount",
        "connectionCount",
        "numConnections",
    }
    posts_keys = {
        "postsCount",
        "postCount",
        "totalPosts",
        "totalPostsCount",
        "numPosts",
    }

    counters: dict[str, tuple[int, str, str] | None] = {
        "followers_count": None,
        "connections_count": None,
        "total_posts_count": None,
    }

    def _set_counter(name: str, value: int, source: str, precision: str) -> None:
        current = counters.get(name)
        if current is None:
            counters[name] = (value, source, precision)
            return
        if current[2] != "exact" and precision == "exact":
            counters[name] = (value, source, precision)

    for item in scan_items:
        stack: list[Any] = [item]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for k, v in current.items():
                    parsed = parse_count_like(v)
                    if parsed is not None:
                        if k in followers_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str)
                                and bool(re.search(r"\d{4,}", v.replace(",", "")))
                            )
                            _set_counter(
                                "followers_count",
                                parsed,
                                f"raw.{k}",
                                "exact" if exact else "estimated",
                            )
                        elif k in connections_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str)
                                and bool(re.search(r"\d{3,}", v.replace(",", "")))
                            )
                            _set_counter(
                                "connections_count",
                                parsed,
                                f"raw.{k}",
                                "exact" if exact else "estimated",
                            )
                        elif k in posts_keys:
                            exact = isinstance(v, (int, float)) or (
                                isinstance(v, str) and bool(re.search(r"\d+", v))
                            )
                            _set_counter(
                                "total_posts_count",
                                parsed,
                                f"raw.{k}",
                                "exact" if exact else "estimated",
                            )
                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(current, list):
                stack.extend(current)

    for item in scan_items:
        stack: list[Any] = [item]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for _, v in current.items():
                    if isinstance(v, str):
                        low = v.lower()
                        m_conn = re.search(
                            r"(\d[\d,\.\s]{1,12})\s*(relations|relation|connections?)", low
                        )
                        if m_conn:
                            parsed = parse_count_like(m_conn.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter(
                                    "connections_count",
                                    parsed,
                                    "raw.text_pattern_connections",
                                    "exact",
                                )

                        m_follow = re.search(
                            r"(\d[\d,\.\s]{1,12})\s*(followers?|abonn[ée]s?)", low
                        )
                        if m_follow:
                            parsed = parse_count_like(m_follow.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter(
                                    "followers_count",
                                    parsed,
                                    "raw.text_pattern_followers",
                                    "exact",
                                )

                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(current, list):
                stack.extend(current)

    def _export(name: str) -> tuple[int | None, str, str]:
        value = counters.get(name)
        if value is None:
            return None, "not_available", "unknown"
        return value

    followers_count, followers_source, followers_precision = _export("followers_count")
    connections_count, connections_source, connections_precision = _export("connections_count")
    total_posts_count, total_posts_source, total_posts_precision = _export("total_posts_count")

    network_size = _pick_network_size(
        followers_count,
        connections_count,
        profile_url=profile_url,
    )

    return {
        "followers_count": network_size,
        "followers_count_source": (
            connections_source if network_size == connections_count else followers_source
        ),
        "followers_count_precision": (
            connections_precision if network_size == connections_count else followers_precision
        ),
        "connections_count": connections_count,
        "connections_count_source": connections_source,
        "connections_count_precision": connections_precision,
        "total_posts_count": total_posts_count,
        "total_posts_count_source": total_posts_source,
        "total_posts_count_precision": total_posts_precision,
    }
