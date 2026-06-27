from __future__ import annotations

import time

import httpx
import pytest
import respx

from lime_mcp_server._cache import JwksCache, JwksSnapshot
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._envelope import JWKS_PATH, METADATA_PATH


def _metadata_body(issuer: str = "https://lime.pics") -> dict:
    return {
        "ok": True,
        "data": {
            "issuer": issuer,
            "jwks_uri": f"https://lime.pics{JWKS_PATH}",
        },
    }


def _jwks_body(jwk: dict) -> dict:
    return {"ok": True, "data": {"keys": [jwk]}}


@respx.mock
def test_jwks_cache_fetch_and_hit(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, cache_ttl=3600)
    cache = JwksCache(config)
    keys1, issuer1 = cache.get_jwks("test-kid")
    keys2, issuer2 = cache.get_jwks("test-kid")
    assert keys1 == keys2
    assert issuer1 == "https://lime.pics"
    assert len(respx.calls) == 2
    cache.close()


@respx.mock
def test_jwks_cache_kid_mismatch_triggers_refresh(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    jwk2 = {**jwk, "kid": "other-kid"}
    base = "https://lime.pics"
    metadata_route = respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    jwks_route = respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, min_refresh_seconds=0)
    cache = JwksCache(config)
    cache.get_jwks("test-kid")

    jwks_route.respond(json=_jwks_body(jwk2))
    keys, _ = cache.get_jwks("other-kid")
    assert any(key.get("kid") == "other-kid" for key in keys)
    assert metadata_route.call_count >= 2
    cache.close()


@respx.mock
def test_jwks_cache_stale_fallback_on_refresh_failure(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, cache_ttl=1)
    cache = JwksCache(config)
    cache.get_jwks("test-kid")

    cache._snapshot = JwksSnapshot(keys=[jwk], issuer="https://lime.pics", fetched_at=0.0)
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=503)
    keys, issuer = cache.get_jwks("test-kid")
    assert keys == [jwk]
    assert issuer == "https://lime.pics"
    cache.close()


@respx.mock
def test_jwks_cache_invalidate_and_warm(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base)
    cache = JwksCache(config)
    cache.warm()
    cache.invalidate()
    assert cache._current_snapshot() is None
    cache.close()


@respx.mock
def test_jwks_cache_missing_issuer() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json={"ok": True, "data": {"issuer": ""}})
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="missing issuer"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_cross_origin_jwks_uri() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        json={
            "ok": True,
            "data": {
                "issuer": "https://lime.pics",
                "jwks_uri": "https://other.example/jwks",
            },
        },
    )
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="cross-origin"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_anti_ddos_skips_forced_refresh(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, min_refresh_seconds=3600)
    cache = JwksCache(config)
    cache.refresh(force=True)
    first_fetched = cache._current_snapshot()
    assert first_fetched is not None
    cache.refresh(force=True)
    assert cache._current_snapshot() is first_fetched
    cache.close()


@respx.mock
def test_jwks_cache_jwks_http_error() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(status_code=500)
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(RuntimeError, match="jwks HTTP"):
        cache.refresh(force=True)
    cache.close()


def test_jwks_snapshot_expired() -> None:
    config = LimeConfig(cache_ttl=1)
    cache = JwksCache(config)
    snapshot = JwksSnapshot(keys=[], issuer="https://lime.pics", fetched_at=time.monotonic() - 10)
    assert cache._is_expired(snapshot)
    cache.close()


@respx.mock
def test_jwks_cache_injected_client(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))
    client = httpx.Client(timeout=30.0, trust_env=False)
    cache = JwksCache(LimeConfig(base_url=base), http_client=client)
    cache.get_jwks("test-kid")
    cache.close()
    client.close()
