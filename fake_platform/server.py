"""
Fake Social Platform Server.

Simulates everything a real platform (Instagram/X) would do, so the main
app can be built and tested WITHOUT ever touching a real account:

  - OAuth token issuance (fake, instant)
  - POST /{platform}/publish
      * honors an Idempotency-Key header: same key replayed -> same
        platform_post_id returned, no new post created
      * randomly returns 429 with Retry-After on the FIRST attempt for a
        given key, to force real backoff/retry handling
      * on success, schedules an async signed webhook delivery to the
        caller's registered webhook_url after a short delay
  - Delivery webhooks are HMAC-SHA256 signed with WEBHOOK_SECRET so the
    receiver can verify authenticity and reject forgeries.

Run standalone: uvicorn fake_platform.server:app --port 9000
"""
import os
import hmac
import hashlib
import json
import random
import time
import uuid
import threading
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Fake Social Platform")

WEBHOOK_SECRET = os.getenv("FAKE_PLATFORM_WEBHOOK_SECRET", "dev-webhook-secret-change-me")

# idempotency_key -> {"platform_post_id": ..., "attempted": bool}
_publish_store: dict[str, dict] = {}
_lock = threading.Lock()


class PublishRequest(BaseModel):
    platform: str
    caption: str
    image_url: str
    webhook_url: str


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str


@app.post("/oauth/token")
def issue_token(req: TokenRequest):
    # Fake OAuth: any non-empty client_id/secret gets a token.
    if not req.client_id or not req.client_secret:
        raise HTTPException(400, "client_id and client_secret required")
    return {
        "access_token": f"fake_token_{uuid.uuid4().hex}",
        "token_type": "bearer",
        "expires_in": 3600,
    }


def _sign_payload(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hmac.new(WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _deliver_webhook_later(webhook_url: str, payload: dict, delay_seconds: float = 2.0):
    def _send():
        time.sleep(delay_seconds)
        signature = _sign_payload(payload)
        try:
            requests.post(
                webhook_url,
                json=payload,
                headers={"X-Signature": signature},
                timeout=5,
            )
        except requests.RequestException:
            pass  # fake platform doesn't retry deliveries; that's the receiver's problem

    threading.Thread(target=_send, daemon=True).start()


@app.post("/{platform}/publish")
def publish(platform: str, req: PublishRequest, idempotency_key: str = Header(..., alias="Idempotency-Key")):
    with _lock:
        existing = _publish_store.get(idempotency_key)

        if existing and existing.get("platform_post_id"):
            # Already succeeded once -- return the SAME post id. No new post.
            return {
                "platform_post_id": existing["platform_post_id"],
                "status": "accepted",
                "replayed": True,
            }

        first_attempt = existing is None
        if first_attempt:
            _publish_store[idempotency_key] = {"platform_post_id": None, "attempted": True}

        # Simulate rate limiting on ~30% of first attempts.
        if first_attempt and random.random() < 0.3:
            return _rate_limited_response()

        platform_post_id = f"{platform}_post_{uuid.uuid4().hex[:10]}"
        _publish_store[idempotency_key]["platform_post_id"] = platform_post_id

    # Schedule async delivery webhook (simulates real platform's eventual delivery).
    # Small random chance of simulated delivery failure.
    delivered_status = "failed" if random.random() < 0.1 else "published"
    _deliver_webhook_later(
        req.webhook_url,
        {
            "event": "delivery",
            "platform": platform,
            "platform_post_id": platform_post_id,
            "idempotency_key": idempotency_key,
            "status": delivered_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {"platform_post_id": platform_post_id, "status": "accepted", "replayed": False}


def _rate_limited_response():
    from fastapi.responses import JSONResponse
    retry_after = 3  # kept short for demo purposes
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "retry_after": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


@app.post("/_debug/forge-webhook")
def forge_webhook(webhook_url: str):
    """Demo helper: sends an UNSIGNED/badly-signed webhook so you can show it getting rejected."""
    payload = {
        "event": "delivery",
        "platform": "instagram",
        "platform_post_id": "forged_post_id",
        "idempotency_key": "forged",
        "status": "published",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        requests.post(webhook_url, json=payload, headers={"X-Signature": "not-a-real-signature"}, timeout=5)
    except requests.RequestException:
        pass
    return {"sent": True}