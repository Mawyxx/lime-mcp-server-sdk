"""Production-style warmup + async verify (wire into your framework)."""

from __future__ import annotations

from contextlib import asynccontextmanager

from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="tools.example.com")


@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    verifier.warmup(raise_on_failure=True)  # raises on JWKS failure
    yield


async def verify_bearer(authorization: str) -> str | None:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    result = await verifier.verify_async(token)
    if not result.is_valid:
        return None
    return result.agent_id
