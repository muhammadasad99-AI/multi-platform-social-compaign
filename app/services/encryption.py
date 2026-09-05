"""
Encrypts OAuth tokens at rest using AES-256-GCM.

Rule: every encryption call generates a FRESH random nonce (IV).
Reusing a nonce with the same key breaks AES-GCM's security guarantees
completely -- so we never accept a caller-supplied nonce, only generate
our own with os.urandom.
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12  # 96 bits, recommended for GCM


def _get_key() -> bytes:
    key_b64 = os.getenv("TOKEN_ENCRYPTION_KEY")
    if not key_b64:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not set. Generate one with: "
            "python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must decode to exactly 32 bytes (AES-256).")
    return key


def encrypt_token(plaintext_token: str) -> tuple[str, str]:
    """Returns (encrypted_token_b64, nonce_b64). Never logs the plaintext."""
    key = _get_key()
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext_token.encode("utf-8"), associated_data=None)
    return (
        base64.b64encode(ciphertext).decode("utf-8"),
        base64.b64encode(nonce).decode("utf-8"),
    )


def decrypt_token(encrypted_token_b64: str, nonce_b64: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    ciphertext = base64.b64decode(encrypted_token_b64)
    nonce = base64.b64decode(nonce_b64)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")