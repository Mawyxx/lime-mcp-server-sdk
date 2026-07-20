from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(name: str, default: str) -> int:
    return int(os.environ.get(name, default))


def _env_expected_domain() -> str | None:
    raw = os.environ.get("LIME_EXPECTED_DOMAIN", "").strip()
    return raw or None


@dataclass(frozen=True, slots=True)
class LimeConfig:
    """Configuration for MCP JWT verification against LIME Core JWKS."""

    base_url: str = field(
        default_factory=lambda: os.environ.get("LIME_BASE_URL", "https://lime.pics").rstrip("/"),
    )
    audience: str = field(
        default_factory=lambda: os.environ.get("LIME_OAUTH_AUDIENCE", "mcp"),
    )
    cache_ttl: int = field(
        default_factory=lambda: _env_int("LIME_JWKS_CACHE_TTL_SECONDS", "3600"),
    )
    leeway_seconds: int = field(
        default_factory=lambda: _env_int("LIME_JWT_VERIFY_LEEWAY_SECONDS", "120"),
    )
    min_refresh_seconds: int = field(
        default_factory=lambda: _env_int("LIME_JWKS_MIN_REFRESH_SECONDS", "60"),
    )
    allowed_algorithms: tuple[str, ...] = ("RS256",)
    user_agent: str = field(
        default_factory=lambda: os.environ.get("LIME_VERIFY_USER_AGENT", "curl/8.5.0"),
    )
    http_timeout: float = 30.0
    # Optional on LimeConfig; TokenVerifier requires a resolved pin (kwarg / config / env).
    expected_domain: str | None = field(default_factory=_env_expected_domain)
