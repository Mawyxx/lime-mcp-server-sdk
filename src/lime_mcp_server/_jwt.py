from __future__ import annotations

from typing import Any, cast

import jwt
from jwt.algorithms import RSAAlgorithm

from lime_mcp_server._claims import McpAccessTokenClaims
from lime_mcp_server._envelope import FORBIDDEN_MCP_CLAIMS


def verify_mcp_access_token(
    token: str,
    *,
    issuer: str,
    audience: str,
    jwks_keys: list[dict[str, Any]],
    leeway_seconds: int = 120,
    allowed_algorithms: tuple[str, ...] = ("RS256",),
) -> McpAccessTokenClaims:
    """Verify RS256 MCP access token against pre-fetched JWKS keys."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    matching = [key for key in jwks_keys if key.get("kid") == kid]
    if not matching:
        raise jwt.InvalidTokenError(f"no jwks key for kid={kid!r}")
    public_key = cast(Any, RSAAlgorithm.from_jwk(matching[0]))
    claims = jwt.decode(
        token,
        public_key,
        algorithms=list(allowed_algorithms),
        issuer=issuer,
        audience=audience,
        leeway=leeway_seconds,
    )
    for forbidden in FORBIDDEN_MCP_CLAIMS:
        if forbidden in claims:
            raise jwt.InvalidTokenError(f"forbidden claim: {forbidden}")
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise jwt.InvalidTokenError("missing sub claim")
    return cast(McpAccessTokenClaims, claims)
