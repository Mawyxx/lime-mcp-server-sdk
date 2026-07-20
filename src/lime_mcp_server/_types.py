from __future__ import annotations

from dataclasses import dataclass

from lime_mcp_server._claims import McpAccessTokenClaims


@dataclass(frozen=True, slots=True)
class TokenValidationResult:
    """Structured outcome of ``TokenVerifier.verify()``.

    Does not raise on invalid tokens — inspect ``is_valid`` and ``error``.

    Attributes:
        is_valid: ``True`` when JWT passed signature, issuer, audience, expiry,
            and domain-binding checks.
        claims: Decoded payload when valid; ``None`` otherwise.
        error: Short reason when ``is_valid`` is ``False``; ``None`` on success.
    """

    is_valid: bool
    claims: McpAccessTokenClaims | None = None
    error: str | None = None

    @property
    def agent_id(self) -> str | None:
        """Agent UUID from ``sub`` claim (MCP OAuth has no separate ``agent_id`` claim)."""
        if self.is_valid and self.claims:
            sub = self.claims.get("sub")
            if isinstance(sub, str) and sub.strip():
                return sub
        return None

    @property
    def domain(self) -> str | None:
        """Normalized ``domain`` claim when verification succeeded."""
        if self.is_valid and self.claims:
            domain = self.claims.get("domain")
            if isinstance(domain, str) and domain.strip():
                return domain
        return None

    @property
    def valid_claims(self) -> McpAccessTokenClaims | None:
        """Narrowed claims when verification succeeded."""
        if self.is_valid and self.claims is not None:
            return self.claims
        return None
