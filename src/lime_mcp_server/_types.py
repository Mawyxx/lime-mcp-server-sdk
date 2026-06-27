from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from lime_mcp_server._claims import McpAccessTokenClaims


@dataclass(frozen=True, slots=True)
class TokenValidationResult:
    """Structured outcome of MCP JWT verification."""

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
    def valid_claims(self) -> McpAccessTokenClaims | None:
        """Narrowed claims when verification succeeded."""
        if self.is_valid and self.claims is not None:
            return cast(McpAccessTokenClaims, self.claims)
        return None
