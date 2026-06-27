from __future__ import annotations

from typing import Any

METADATA_PATH = "/api/v1/modules/oauth/.well-known/oauth-authorization-server"
JWKS_PATH = "/api/v1/core/.well-known/jwks.json"

FORBIDDEN_MCP_CLAIMS = frozenset({"user_id", "passport_version", "request_id"})


def unwrap_lime_data(body: dict[str, Any]) -> dict[str, Any]:
    """Unwrap LIME API envelope ``{ ok, data }``."""
    if not body.get("ok"):
        raise ValueError("LIME envelope not ok")
    data = body.get("data")
    if not isinstance(data, dict):
        raise ValueError("LIME envelope missing data object")
    return data
