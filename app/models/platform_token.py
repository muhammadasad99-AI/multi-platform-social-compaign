import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class PlatformToken(Base):
    """
    OAuth access token per platform, encrypted at rest with AES-GCM.
    We never store the plaintext token in the DB or in logs -- only
    ciphertext + the nonce needed to decrypt it.
    """
    __tablename__ = "platform_tokens"

    id = Column(String, primary_key=True, default=gen_uuid)
    platform = Column(String, nullable=False, unique=True)  # "instagram" | "x"

    encrypted_token = Column(String, nullable=False)  # base64 ciphertext
    nonce = Column(String, nullable=False)             # base64 random IV/nonce

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )