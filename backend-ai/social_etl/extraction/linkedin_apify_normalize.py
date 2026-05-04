"""
Post-traitement des items renvoyés par un acteur Apify LinkedIn (profil / posts).

Logique pure, sans HTTP ni OAuth — utilisé par ``linkedin_extractor``.
"""

from __future__ import annotations

import re
from typing import Any


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


def normalize_linkedin_apify_items(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Aligne les posts Apify sur le schéma historique ``linkedin_extract_result.json``."""
    posts: list[dict[str, Any]] = []
    for item in items[:limit]:
        raw_type = str(item.get("type") or "").strip().lower()
        post_type_api = raw_type if raw_type else "unknown"
        comments_count, comments_list = _linkedin_comments_count_and_list(item)
        row: dict[str, Any] = {
            "id": item.get("id") or item.get("postId"),
            "post_type_api": post_type_api,
            "text": item.get("text") or item.get("content") or item.get("postText"),
            "published_at": item.get("postedAt") or item.get("timestamp") or item.get("date"),
            "post_url": item.get("postUrl") or item.get("url"),
            "likes": item.get("likes") or item.get("numLikes"),
            "comments": comments_count,
            "reposts": item.get("reposts") or item.get("numShares") or item.get("shares"),
            "raw": item,
        }
        if comments_list:
            row["comments_list"] = comments_list
        posts.append(row)
    return posts


def extract_linkedin_profile_counters(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Déduit followers / connexions / nombre de posts depuis le payload Apify."""
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

    for item in items:
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

    for item in items:
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

                        m_posts = re.search(r"(\d[\d,\.\s]{1,12})\s*(posts?|publications?)", low)
                        if m_posts:
                            parsed = parse_count_like(m_posts.group(1).replace(" ", ""))
                            if parsed is not None:
                                _set_counter(
                                    "total_posts_count",
                                    parsed,
                                    "raw.text_pattern_posts",
                                    "exact",
                                )

                    if isinstance(v, (dict, list)):
                        stack.append(v)
            elif isinstance(current, list):
                stack.extend(current)

    for item in items:
        author = item.get("author")
        if isinstance(author, dict):
            info = author.get("info")
            if isinstance(info, str):
                m = re.search(r"\+?\d+(?:\.\d+)?[kKmM]", info)
                if m:
                    parsed = parse_count_like(m.group(0))
                    if parsed is not None and counters["followers_count"] is None:
                        _set_counter(
                            "followers_count", parsed, "author.info_heuristic", "estimated"
                        )

    def _export(name: str) -> tuple[int | None, str, str]:
        value = counters.get(name)
        if value is None:
            return None, "not_available", "unknown"
        return value

    followers_count, followers_source, followers_precision = _export("followers_count")
    connections_count, connections_source, connections_precision = _export("connections_count")
    total_posts_count, total_posts_source, total_posts_precision = _export("total_posts_count")

    return {
        "followers_count": followers_count,
        "followers_count_source": followers_source,
        "followers_count_precision": followers_precision,
        "connections_count": connections_count,
        "connections_count_source": connections_source,
        "connections_count_precision": connections_precision,
        "total_posts_count": total_posts_count,
        "total_posts_count_source": total_posts_source,
        "total_posts_count_precision": total_posts_precision,
    }
