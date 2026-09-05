"""
The SocialPublisher interface. The rest of the application depends ONLY
on this contract -- never on a specific platform. Adding a new platform
means writing a new adapter class, not touching any calling code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PublishResult:
    platform_post_id: str
    idempotency_key: str
    status: str  # "accepted" -- final status only ever comes from the webhook


class RateLimitedError(Exception):
    """Raised when the platform returns 429. Carries the Retry-After (seconds)."""
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limited, retry after {retry_after_seconds}s")


class SocialPublisher(ABC):
    platform_name: str

    @abstractmethod
    def publish(self, *, idempotency_key: str, image_path: str, caption: str) -> PublishResult:
        """
        Publish a post. MUST be safe to call twice with the same
        idempotency_key -- the platform (real or fake) is responsible for
        collapsing retries into a single logical post, and this method
        must pass that key through on every call, including retries.

        Raises RateLimitedError on 429 so the caller can back off.
        """
        raise NotImplementedError