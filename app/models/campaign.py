import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Campaign(Base):
    """A campaign wraps one blog post -> N platform posts (SocialPostEntry rows)."""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=gen_uuid)
    blog_title = Column(String, nullable=False)
    blog_body = Column(Text, nullable=False)
    blog_url = Column(String, nullable=False)
    source_image_path = Column(String, nullable=True)

    # ISO datetime string for when the campaign should go live. Null = publish ASAP.
    scheduled_for = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))