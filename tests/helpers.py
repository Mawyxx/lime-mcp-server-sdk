from __future__ import annotations

import time
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keypair() -> tuple[Any, dict[str, Any]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": "test-kid",
        "use": "sig",
        "alg": "RS256",
        "n": jwt.utils.base64url_encode(
            public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big"),
        ).decode(),
        "e": jwt.utils.base64url_encode(
            public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big"),
        ).decode(),
    }
    return private_key, jwk


def sign_mcp_token(
    private_key: Any,
    *,
    kid: str = "test-kid",
    sub: str = "agent-uuid",
    issuer: str = "https://lime.pics",
    audience: str = "mcp",
    exp_offset: int = 3600,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": sub,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + exp_offset,
        "jti": "test-jti",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )
