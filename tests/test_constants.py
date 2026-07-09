from __future__ import annotations

from lime_mcp_server._constants import FORBIDDEN_MCP_CLAIMS, JWKS_PATH, METADATA_PATH


def test_forbidden_mcp_claims_frozen() -> None:
    assert "user_id" in FORBIDDEN_MCP_CLAIMS
    assert "request_id" in FORBIDDEN_MCP_CLAIMS


def test_well_known_paths() -> None:
    assert JWKS_PATH.endswith("jwks.json")
    assert "oauth-authorization-server" in METADATA_PATH
