"""
API-level idempotency (Stripe-style): a client can send an
Idempotency-Key header on POST /campaigns/{id}/publish. If the same key
is replayed (e.g. because the client never saw the response due to a
network timeout), we return the stored response instead of re-running
the publish logic.

This is deliberately a SEPARATE concept from SocialPostEntry.idempotency_key,
which is the key we hand to the fake platform so ITS retries collapse too.
Two layers of idempotency: ours (client <-> us) and theirs (us <-> platform).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String, primary_key=True, default=gen_uuid)
    key = Column(String, nullable=False, unique=True, index=True)
    request_path = Column(String, nullable=False)
    response_status = Column(Integer, nullable=False)
    response_body = Column(Text, nullable=False)  # JSON-serialized
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))