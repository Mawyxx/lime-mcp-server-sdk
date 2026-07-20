from __future__ import annotations

from typing import Any, cast

import jwt
from jwt.algorithms import RSAAlgorithm

from lime_mcp_server._claims import McpAccessTokenClaims
from lime_mcp_server._constants import FORBIDDEN_MCP_CLAIMS
from lime_mcp_server._domain import normalize_mcp_domain

_ERR_MISSING_DOMAIN = "Missing domain claim"
_ERR_INVALID_DOMAIN_CLAIM = "Invalid domain claim"
_ERR_DOMAIN_MISMATCH = "Domain mismatch"


def verify_mcp_access_token(
    token: str,
    *,
    issuer: str,
    audience: str,
    jwks_keys: list[dict[str, Any]],
    expected_domain: str,
    leeway_seconds: int = 120,
    allowed_algorithms: tuple[str, ...] = ("RS256",),
) -> McpAccessTokenClaims:
    """Verify RS256 MCP access token against pre-fetched JWKS keys + domain pin."""
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

    raw_domain = claims.get("domain")
    if not isinstance(raw_domain, str) or not raw_domain.strip():
        raise jwt.InvalidTokenError(_ERR_MISSING_DOMAIN)

    try:
        normalized_claim = normalize_mcp_domain(raw_domain)
    except ValueError as exc:
        raise jwt.InvalidTokenError(_ERR_INVALID_DOMAIN_CLAIM) from exc

    # Core mints canonical lowercase hostnames only; reject scheme/path/case drift.
    if normalized_claim != raw_domain:
        raise jwt.InvalidTokenError(_ERR_INVALID_DOMAIN_CLAIM)

    if normalized_claim != expected_domain:
        raise jwt.InvalidTokenError(_ERR_DOMAIN_MISMATCH)

    return cast(McpAccessTokenClaims, claims)
