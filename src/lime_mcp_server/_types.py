from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TokenValidationResult:
    """Structured outcome of MCP JWT verification."""

    is_valid: bool
    claims: dict[str, Any] | None = None
    error: str | None = None

    @property
    def agent_id(self) -> str | None:
        """Agent UUID from ``sub`` claim (MCP OAuth has no separate ``agent_id`` claim)."""
        if self.is_valid and self.claims:
            sub = self.claims.get("sub")
            if isinstance(sub, str) and sub.strip():
                return sub
        return None
