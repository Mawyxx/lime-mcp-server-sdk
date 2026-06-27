from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx

from lime_mcp_server._config import LimeConfig
from lime_mcp_server._envelope import JWKS_PATH, METADATA_PATH, unwrap_lime_data

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
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(
            timeout=config.http_timeout,
            trust_env=False,
            headers={
                "Accept": "application/json",
                "User-Agent": config.user_agent,
            },
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def warm(self) -> None:
        """Prefetch metadata and JWKS (non-fatal on failure)."""
        try:
            self.refresh(force=True)
        except Exception:
            logger.warning("JWKS cache warmup failed", exc_info=True)

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
            self._snapshot = self._fetch_snapshot()

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

    def _fetch_snapshot(self) -> JwksSnapshot:
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
        return unwrap_lime_data(body)

    def _fetch_jwks(self, jwks_uri: str) -> list[dict[str, Any]]:
        base = self._config.base_url
        if jwks_uri.startswith(base):
            path = jwks_uri[len(base) :]
        elif jwks_uri.startswith("http"):
            raise ValueError("cross-origin jwks_uri fetch not supported")
        elif jwks_uri:
            path = jwks_uri
        else:
            path = JWKS_PATH

        response = self._client.get(f"{base}{path}")
        if response.status_code != 200:
            raise RuntimeError(f"jwks HTTP {response.status_code}")
        try:
            body = response.json()
        except ValueError as exc:
            raise ValueError("jwks response must be JSON object") from exc
        if not isinstance(body, dict):
            raise ValueError("jwks response must be JSON object")
        data = unwrap_lime_data(body)
        keys = data.get("keys")
        if not isinstance(keys, list) or not keys:
            raise ValueError("jwks missing keys")
        return keys
