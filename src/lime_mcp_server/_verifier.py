from __future__ import annotations

import asyncio
from typing import Any

import jwt

from lime_mcp_server._cache import JwksCache
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._jwt import verify_mcp_access_token
from lime_mcp_server._types import TokenValidationResult


class TokenVerifier:
    """Verify LIME-issued MCP JWTs for external resource servers."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        audience: str | None = None,
        cache_ttl: int | None = None,
        leeway_seconds: int | None = None,
        min_refresh_seconds: int | None = None,
        allowed_algorithms: tuple[str, ...] | None = None,
        config: LimeConfig | None = None,
        cache: JwksCache | None = None,
    ) -> None:
        defaults = config or LimeConfig()
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
        """Verify a Bearer MCP JWT without blocking the event loop."""
        return await asyncio.to_thread(self.verify, token)

    def verify(self, token: str) -> TokenValidationResult:
        """Verify a Bearer MCP JWT and return a structured result."""
        try:
            kid = self._get_kid(token)
            jwks_keys, issuer = self._cache.get_jwks(kid)
            claims = verify_mcp_access_token(
                token,
                issuer=issuer,
                audience=self._config.audience,
                jwks_keys=jwks_keys,
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
            return TokenValidationResult(is_valid=False, error=f"Invalid token: {exc}")
        except Exception as exc:
            return TokenValidationResult(is_valid=False, error=f"Verification error: {exc}")

    def refresh_cache(self) -> None:
        self._cache.refresh(force=True)

    def invalidate_cache(self) -> None:
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
        self._cache.close()

    def __enter__(self) -> TokenVerifier:
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()
