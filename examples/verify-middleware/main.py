"""Canonical TokenVerifier usage for an MCP resource server."""

from __future__ import annotations

from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="tools.example.com")


def authorize_mcp_request(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    token = authorization_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    result = verifier.verify(token)
    if not result.is_valid:
        return None
    return result.agent_id


if __name__ == "__main__":
    # Demo with an invalid token — expect None
    print(authorize_mcp_request("Bearer not-a-jwt"))
