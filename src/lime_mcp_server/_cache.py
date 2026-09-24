from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from lime_mcp_server._config import LimeConfig
from lime_mcp_server._constants import JWKS_PATH, METADATA_PATH

logger = logging.getLogger("lime.mcp_server")


@dataclass(frozen=True, slots=True)
class JwksSnapshot:
    keys: list[dict[str, Any]]
    issuer: str
    fetched_at: float


class JwksCache:
    """Thread-safe JWKS + OAuth metadata cache with stale fallback."""

    def __init__(
        self,
        config: LimeConfig,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._snapshot: JwksSnapshot | None = None
        self._last_forced_refresh_at: float = 0.0
        self._fetch_count = 0
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=config.http_timeout,
            trust_env=False,
            headers={
                "Accept": "application/json",
                "User-Agent": config.user_agent,
            },
        )

    @property
    def fetch_count(self) -> int:
        """Number of successful metadata+JWKS network fetches."""
        with self._lock:
            return self._fetch_count

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def warm(self) -> bool:
        """Prefetch metadata and JWKS (non-fatal on failure)."""
        try:
            self.refresh(force=True)
            return True
        except Exception:
            logger.warning("JWKS cache warmup failed", exc_info=True)
            return False

    def invalidate(self) -> None:
        with self._lock:
            self._snapshot = None

    def refresh(self, *, force: bool = False) -> None:
        """Refresh metadata + JWKS from LIME."""
        now = time.monotonic()
        with self._lock:
            if force:
                elapsed = now - self._last_forced_refresh_at
                if elapsed < self._config.min_refresh_seconds:
                    if self._snapshot is not None:
                        return
                self._last_forced_refresh_at = now
            self._snapshot = self._fetch_snapshot_uncounted()
            self._fetch_count += 1

    def get_jwks(self, kid: str | None) -> tuple[list[dict[str, Any]], str]:
        """Return JWKS keys and issuer; refresh on TTL expiry or kid mismatch."""
        snapshot = self._current_snapshot()
        if snapshot is None or self._is_expired(snapshot):
            try:
                self.refresh(force=False)
            except Exception as exc:
                if snapshot is not None:
                    logger.warning("JWKS refresh failed, using stale cache: %s", exc)
                    return snapshot.keys, snapshot.issuer
                raise
            snapshot = self._current_snapshot()
            if snapshot is None:
                raise RuntimeError("JWKS cache unavailable after refresh")

        if kid is not None and not any(key.get("kid") == kid for key in snapshot.keys):
            try:
                self.refresh(force=True)
            except Exception as exc:
                logger.warning("JWKS kid-mismatch refresh failed: %s", exc)
                if not any(key.get("kid") == kid for key in snapshot.keys):
                    raise
            snapshot = self._current_snapshot()
            if snapshot is None:
                raise RuntimeError("JWKS cache unavailable after kid refresh")

        return snapshot.keys, snapshot.issuer

    def _current_snapshot(self) -> JwksSnapshot | None:
        with self._lock:
            return self._snapshot

    def _is_expired(self, snapshot: JwksSnapshot) -> bool:
        return (time.monotonic() - snapshot.fetched_at) >= self._config.cache_ttl

    def _fetch_snapshot_uncounted(self) -> JwksSnapshot:
        metadata = self._fetch_metadata()
        issuer = str(metadata.get("issuer", "")).strip()
        if not issuer:
            raise ValueError("metadata missing issuer")
        jwks_uri = str(metadata.get("jwks_uri", ""))
        keys = self._fetch_jwks(jwks_uri)
        return JwksSnapshot(keys=keys, issuer=issuer, fetched_at=time.monotonic())

    def _fetch_metadata(self) -> dict[str, Any]:
        response = self._client.get(f"{self._config.base_url}{METADATA_PATH}")
        if response.status_code != 200:
            raise RuntimeError(f"oauth metadata HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ValueError("metadata response must be JSON object") from exc
        if not isinstance(body, dict):
            raise ValueError("metadata response must be JSON object")
        return _parse_oauth_metadata(body)

    def _resolve_jwks_url(self, jwks_uri: str) -> str:
        """Resolve ``jwks_uri`` to a same-origin URL (exact-origin allowlist).

        Full URLs must match the configured ``base_url`` origin exactly
        (scheme + netloc). Prefix/sibling origins (``https://lime.pics.evil.tld``)
        and userinfo tricks (``https://lime.pics@evil.tld``) are rejected.
        Relative paths are joined onto ``base_url``.
        """
        base = self._config.base_url
        parsed = urlparse(jwks_uri)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("jwks_uri must be an absolute http(s) URL")
            base_parsed = urlparse(base)
            if (parsed.scheme.lower(), parsed.netloc.lower()) != (
                base_parsed.scheme.lower(),
                base_parsed.netloc.lower(),
            ):
                raise ValueError("cross-origin jwks_uri fetch not supported")
            origin = f"{parsed.scheme}://{parsed.netloc}"
            return f"{origin}{parsed.path}" if parsed.path else f"{origin}{JWKS_PATH}"
        if jwks_uri:
            return f"{base}{jwks_uri}" if jwks_uri.startswith("/") else f"{base}/{jwks_uri}"
        return f"{base}{JWKS_PATH}"

    def _fetch_jwks(self, jwks_uri: str) -> list[dict[str, Any]]:
        response = self._client.get(self._resolve_jwks_url(jwks_uri))
        if response.status_code != 200:
            raise RuntimeError(f"jwks HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ValueError("jwks response must be JSON object") from exc
        if not isinstance(body, dict):
            raise ValueError("jwks response must be JSON object")
        keys = body.get("keys")
        if not isinstance(keys, list) or not keys:
            raise ValueError("jwks missing keys")
        return keys


def _parse_oauth_metadata(body: dict[str, Any]) -> dict[str, Any]:
    issuer = str(body.get("issuer", "")).strip()
    if not issuer:
        raise ValueError("metadata missing issuer")
    jwks_uri = str(body.get("jwks_uri", "")).strip()
    if not jwks_uri:
        raise ValueError("metadata missing jwks_uri")
    grant_types = body.get("grant_types_supported")
    if grant_types is not None and not isinstance(grant_types, list):
        raise ValueError("metadata grant_types_supported must be a list")
    return body
