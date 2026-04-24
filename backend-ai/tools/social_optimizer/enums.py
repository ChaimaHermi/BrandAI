from enum import Enum


class Platform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"


class ContentType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    CAROUSEL = "carousel"
    OTHER = "other"

