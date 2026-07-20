from __future__ import annotations

import asyncio
import os
from typing import Any

import jwt

from lime_mcp_server._cache import JwksCache
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._domain import normalize_mcp_domain
from lime_mcp_server._jwt import verify_mcp_access_token
from lime_mcp_server._types import TokenValidationResult

_DOMAIN_RESULT_ERRORS = frozenset(
    {
        "Missing domain claim",
        "Invalid domain claim",
        "Domain mismatch",
    },
)


def _resolve_expected_domain(
    *,
    expected_domain: str | None,
    config: LimeConfig | None,
) -> str:
    """Resolve and normalize RS domain pin (kwarg → config → env)."""
    if expected_domain is not None:
        raw = expected_domain
    elif config is not None and config.expected_domain is not None:
        raw = config.expected_domain
    else:
        raw = os.environ.get("LIME_EXPECTED_DOMAIN", "").strip() or None
        if raw is None and config is None:
            # LimeConfig() already pulled env into expected_domain via default_factory.
            raw = LimeConfig().expected_domain

    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ValueError("expected_domain is required")

    return normalize_mcp_domain(raw)


class TokenVerifier:
    """Verify LIME-issued MCP JWTs for external resource servers.

    Fetches OAuth metadata and Core JWKS with caching. Does not issue tokens — agents
    obtain MCP JWTs via ``lime-agents-sdk``. Requires a domain pin
    (``expected_domain`` or ``LIME_EXPECTED_DOMAIN``) so JWTs minted for other
    resource servers are rejected.

    See `LIME platform docs <https://lime.pics/docs#guide-mcpServerSdk>`_ for HTTP details.
    """

    def __init__(
        self,
        *,
        expected_domain: str | None = None,
        base_url: str | None = None,
        audience: str | None = None,
        cache_ttl: int | None = None,
        leeway_seconds: int | None = None,
        min_refresh_seconds: int | None = None,
        allowed_algorithms: tuple[str, ...] | None = None,
        config: LimeConfig | None = None,
        cache: JwksCache | None = None,
    ) -> None:
        """Create a verifier with a required domain pin.

        Args:
            expected_domain: Hostname this RS serves (URL-ish OK; ports rejected).
                Falls back to ``config.expected_domain`` then ``LIME_EXPECTED_DOMAIN``.
            base_url: LIME origin without ``/api/v1`` (default from ``LIME_BASE_URL``).
            audience: Expected JWT ``aud`` (default ``mcp`` from ``LIME_OAUTH_AUDIENCE``).
            cache_ttl: JWKS cache TTL seconds.
            leeway_seconds: JWT clock skew leeway.
            min_refresh_seconds: Minimum seconds between forced JWKS refreshes.
            allowed_algorithms: JWT algorithms allowed (default ``RS256`` only).
            config: Pre-built ``LimeConfig`` (other args override its fields).
            cache: Optional ``JwksCache`` for tests or shared cache instances.

        Raises:
            ValueError: When no domain pin is configured or normalize rejects it.
        """
        defaults = config or LimeConfig()
        pinned = _resolve_expected_domain(expected_domain=expected_domain, config=defaults)
        self._config = LimeConfig(
            base_url=(base_url or defaults.base_url).rstrip("/"),
            audience=audience or defaults.audience,
            cache_ttl=cache_ttl if cache_ttl is not None else defaults.cache_ttl,
            leeway_seconds=(
                leeway_seconds if leeway_seconds is not None else defaults.leeway_seconds
            ),
            min_refresh_seconds=(
                min_refresh_seconds
                if min_refresh_seconds is not None
                else defaults.min_refresh_seconds
            ),
            allowed_algorithms=allowed_algorithms or defaults.allowed_algorithms,
            user_agent=defaults.user_agent,
            http_timeout=defaults.http_timeout,
            expected_domain=pinned,
        )
        self._cache = cache or JwksCache(self._config)
        self._cache.warm()

    @property
    def config(self) -> LimeConfig:
        return self._config

    @property
    def cache(self) -> JwksCache:
        return self._cache

    def warmup(self, *, raise_on_failure: bool = False) -> bool:
        """Prefetch OAuth metadata and JWKS."""
        if raise_on_failure:
            self._cache.refresh(force=True)
            return True
        return self._cache.warm()

    async def verify_async(self, token: str) -> TokenValidationResult:
        """Verify a Bearer MCP JWT without blocking the event loop.

        Args:
            token: Raw JWT string (without ``Bearer `` prefix).

        Returns:
            ``TokenValidationResult`` with ``is_valid``, ``claims``, and ``error``.
        """
        return await asyncio.to_thread(self.verify, token)

    def verify(self, token: str) -> TokenValidationResult:
        """Verify a Bearer MCP JWT and return a structured result.

        Args:
            token: Raw JWT string (without ``Bearer `` prefix).

        Returns:
            ``TokenValidationResult`` — use ``agent_id`` / ``domain`` when valid.
        """
        expected = self._config.expected_domain
        if expected is None:  # pragma: no cover — enforced at construct
            raise ValueError("expected_domain is required")
        try:
            kid = self._get_kid(token)
            jwks_keys, issuer = self._cache.get_jwks(kid)
            claims = verify_mcp_access_token(
                token,
                issuer=issuer,
                audience=self._config.audience,
                jwks_keys=jwks_keys,
                expected_domain=expected,
                leeway_seconds=self._config.leeway_seconds,
                allowed_algorithms=self._config.allowed_algorithms,
            )
            return TokenValidationResult(is_valid=True, claims=claims, error=None)
        except jwt.ExpiredSignatureError:
            return TokenValidationResult(is_valid=False, error="Token expired")
        except jwt.InvalidIssuerError:
            return TokenValidationResult(is_valid=False, error="Invalid issuer")
        except jwt.InvalidAudienceError:
            return TokenValidationResult(is_valid=False, error="Invalid audience")
        except jwt.InvalidTokenError as exc:
            message = str(exc)
            if message in _DOMAIN_RESULT_ERRORS:
                return TokenValidationResult(is_valid=False, error=message)
            return TokenValidationResult(is_valid=False, error=f"Invalid token: {exc}")
        except Exception as exc:
            return TokenValidationResult(is_valid=False, error=f"Verification error: {exc}")

    def refresh_cache(self) -> None:
        """Force-refresh OAuth metadata and JWKS from LIME."""
        self._cache.refresh(force=True)

    def invalidate_cache(self) -> None:
        """Drop cached JWKS snapshot (next verify triggers fetch)."""
        self._cache.invalidate()

    @staticmethod
    def _get_kid(token: str) -> str | None:
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            return str(kid) if kid is not None else None
        except Exception:
            return None

    def close(self) -> None:
        """Release HTTP resources held by the JWKS cache."""
        self._cache.close()

    def __enter__(self) -> TokenVerifier:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
