from __future__ import annotations

import os

import httpx
import pytest

from lime_mcp_server import TokenVerifier


@pytest.mark.integration
def test_live_lime_jwks_warmup() -> None:
    if os.environ.get("LIME_MCP_SERVER_INTEGRATION") != "1":
        pytest.skip("set LIME_MCP_SERVER_INTEGRATION=1 for live JWKS test")

    base = os.environ.get("LIME_BASE_URL", "https://lime.pics").rstrip("/")
    verifier = TokenVerifier(base_url=base)
    try:
        verifier.refresh_cache()
    finally:
        verifier.close()


@pytest.mark.integration
def test_live_verify_mcp_token() -> None:
    if os.environ.get("LIME_MCP_SERVER_INTEGRATION") != "1":
        pytest.skip("set LIME_MCP_SERVER_INTEGRATION=1")

    agent_token = os.environ.get("LIME_AGENT_TOKEN", "").strip()
    if not agent_token:
        pytest.skip("LIME_AGENT_TOKEN required")

    base = os.environ.get("LIME_BASE_URL", "https://lime.pics").rstrip("/")
    api_base = os.environ.get("LIME_API_BASE", f"{base}/api/v1").rstrip("/")

    response = httpx.post(
        f"{api_base}/modules/oauth/token",
        headers={"X-Agent-Token": agent_token},
        timeout=30.0,
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]

    verifier = TokenVerifier(base_url=base)
    try:
        result = verifier.verify(access_token)
    finally:
        verifier.close()

    assert result.is_valid is True
    assert result.agent_id is not None
