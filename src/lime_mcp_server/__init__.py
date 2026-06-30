"""LIME MCP resource server SDK — JWT verification via Core JWKS."""

from __future__ import annotations

from lime_mcp_server._cache import JwksCache
from lime_mcp_server._claims import McpAccessTokenClaims
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._envelope import FORBIDDEN_MCP_CLAIMS, unwrap_lime_data
from lime_mcp_server._jwt import verify_mcp_access_token
from lime_mcp_server._types import TokenValidationResult
from lime_mcp_server._verifier import TokenVerifier

__version__ = "0.4.0"

__all__ = [
    "FORBIDDEN_MCP_CLAIMS",
    "JwksCache",
    "LimeConfig",
    "McpAccessTokenClaims",
    "TokenValidationResult",
    "TokenVerifier",
    "jwks_cache_ttl_seconds",
    "unwrap_lime_data",
    "verify_mcp_access_token",
]


def jwks_cache_ttl_seconds() -> int:
    """Default JWKS cache TTL from environment (compatibility helper)."""
    return LimeConfig().cache_ttl
