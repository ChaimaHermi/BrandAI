"""Constantes Graph API (insights) partagées par les extracteurs Meta."""

from __future__ import annotations

FACEBOOK_PAGE_INSIGHT_METRICS = [
    "page_impressions_unique",
    "page_post_engagements",
    "page_views_total",
    "page_fans_online",
    "page_actions_post_reactions_total",
    "page_actions_post_comments_total",
    "page_actions_post_shares_total",
    "page_impressions",
]

FACEBOOK_POST_INSIGHT_METRICS = [
    "post_impressions_unique",
    "post_clicks",
    "post_reactions_like_total",
    "post_reactions_love_total",
    "post_reactions_wow_total",
    "post_reactions_haha_total",
    "post_reactions_sorry_total",
    "post_reactions_anger_total",
    "post_video_views",
    "post_video_complete_views_organic",
    "post_impressions_paid",
    "post_impressions_fan",
    "post_impressions_organic",
    "post_impressions",
    "post_engaged_users",
    "post_comments",
    "post_shares",
]

INSTAGRAM_ACCOUNT_INSIGHT_METRICS = [
    "impressions",
    "reach",
    "profile_views",
    "website_clicks",
    "follower_count",
    "online_followers",
]

INSTAGRAM_MEDIA_INSIGHT_METRICS = [
    "impressions",
    "reach",
    "engagement",
    "saved",
    "shares",
    "video_views",
    "plays",
    "total_interactions",
]
