from __future__ import annotations

METADATA_PATH = "/api/v1/modules/oauth/.well-known/oauth-authorization-server"
JWKS_PATH = "/api/v1/core/.well-known/jwks.json"

FORBIDDEN_MCP_CLAIMS = frozenset({"user_id", "passport_version", "request_id"})
