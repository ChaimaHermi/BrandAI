from datetime import datetime

from pydantic import BaseModel, Field

from tools.social_optimizer.enums import ContentType, Platform


class NormalizedPostMetric(BaseModel):
    idea_id: int
    platform: Platform
    external_post_id: str
    published_at: datetime
    content_type: ContentType = ContentType.OTHER

    reach: int = 0
    impressions: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0

    engagement_rate: float = Field(default=0.0, ge=0.0)
    collected_at: datetime

