from __future__ import annotations

from typing import TypedDict


class McpAccessTokenClaims(TypedDict):
    """MCP OAuth JWT claim set issued by LIME (ADR 0081)."""

    sub: str
    iss: str
    aud: str
    iat: int
    exp: int
    jti: str
