"""
One concrete adapter class parameterized by platform name, since both
FakeInstagramPublisher and FakeXPublisher talk to the same fake server
with the same protocol. Each is still exposed as its own class so the
app can type/inject them distinctly and so a future REAL adapter for
one platform doesn't force changes to the other.
"""
import os
import requests
from app.adapters.base import SocialPublisher, PublishResult, RateLimitedError

FAKE_PLATFORM_URL = os.getenv("FAKE_PLATFORM_URL", "http://localhost:9000")
WEBHOOK_CALLBACK_URL = os.getenv("WEBHOOK_CALLBACK_URL", "http://localhost:8000/webhooks/social-delivery")


class _FakePlatformAdapterBase(SocialPublisher):
    def publish(self, *, idempotency_key: str, image_path: str, caption: str) -> PublishResult:
        response = requests.post(
            f"{FAKE_PLATFORM_URL}/{self.platform_name}/publish",
            json={
                "platform": self.platform_name,
                "caption": caption,
                "image_url": image_path,  # local path stands in for a hosted URL in this sandbox
                "webhook_url": WEBHOOK_CALLBACK_URL,
            },
            headers={"Idempotency-Key": idempotency_key},
            timeout=10,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            raise RateLimitedError(retry_after)

        response.raise_for_status()
        data = response.json()
        return PublishResult(
            platform_post_id=data["platform_post_id"],
            idempotency_key=idempotency_key,
            status="accepted",
        )


class FakeInstagramPublisher(_FakePlatformAdapterBase):
    platform_name = "instagram"


class FakeXPublisher(_FakePlatformAdapterBase):
    platform_name = "x"


def get_publisher(platform: str) -> SocialPublisher:
    registry = {
        "instagram": FakeInstagramPublisher(),
        "x": FakeXPublisher(),
    }
    if platform not in registry:
        raise ValueError(f"No publisher registered for platform '{platform}'")
    return registry[platform]