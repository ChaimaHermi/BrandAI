def compute_engagement_rate(
    impressions: int,
    likes: int,
    comments: int,
    shares: int,
) -> float:
    impressions = max(int(impressions or 0), 0)
    likes = max(int(likes or 0), 0)
    comments = max(int(comments or 0), 0)
    shares = max(int(shares or 0), 0)

    if impressions == 0:
        return 0.0
    return round(((likes + comments + shares) / impressions) * 100, 2)

