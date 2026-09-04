import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Integer
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class PostStatus(str, enum.Enum):
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class SocialPostEntry(Base):
    """
    One row per (campaign, platform). This is the single source of truth
    for publish state. Status may ONLY move to PUBLISHED or FAILED as a
    result of a signature-verified webhook event -- never optimistically
    from the publish call itself.
    """
    __tablename__ = "social_post_entries"

    id = Column(String, primary_key=True, default=gen_uuid)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=False)
    platform = Column(String, nullable=False)  # "instagram" | "x"

    image_path = Column(String, nullable=True)
    caption = Column(Text, nullable=True)

    status = Column(Enum(PostStatus), default=PostStatus.QUEUED, nullable=False)

    # The key WE generate and send to the fake platform so retries collapse
    # into a single logical publish. One idempotency key per (campaign, platform).
    idempotency_key = Column(String, nullable=False, unique=True)

    # The platform's own post id, filled in once we get a confirmed response.
    platform_post_id = Column(String, nullable=True)

    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )