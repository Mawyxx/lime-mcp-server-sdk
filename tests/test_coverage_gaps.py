from __future__ import annotations

import time

import pytest
import respx

from lime_mcp_server._cache import JwksCache, JwksSnapshot
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._envelope import JWKS_PATH, METADATA_PATH
from lime_mcp_server._types import TokenValidationResult
from lime_mcp_server._verifier import TokenVerifier
from tests.helpers import sign_mcp_token


def _metadata_body() -> dict:
    return {
        "issuer": "https://lime.pics",
        "token_endpoint": "https://lime.pics/api/v1/modules/oauth/token",
        "jwks_uri": f"https://lime.pics{JWKS_PATH}",
        "grant_types_supported": ["client_credentials"],
    }


@respx.mock
def test_jwks_cache_metadata_http_error() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=500)
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(RuntimeError, match="oauth metadata HTTP"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_jwks_missing_keys() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": []}})
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="jwks missing keys"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_jwks_invalid_json() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(text="not-json", headers={"Content-Type": "text/plain"})
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_jwks_non_object_json() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=[])
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="JSON object"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_metadata_invalid_json() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        text="not-json",
        headers={"Content-Type": "text/plain"},
    )
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="metadata response must be JSON object"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_metadata_non_object() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=[])
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="metadata response"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_metadata_lime_envelope_rejected() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        json={
            "ok": True,
            "data": {
                "issuer": "https://lime.pics",
                "jwks_uri": f"https://lime.pics{JWKS_PATH}",
            },
        },
    )
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="metadata missing issuer"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_jwks_cache_relative_jwks_uri(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        json={
            "issuer": "https://lime.pics",
            "token_endpoint": "https://lime.pics/api/v1/modules/oauth/token",
            "jwks_uri": JWKS_PATH,
            "grant_types_supported": ["client_credentials"],
        },
    )
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})
    cache = JwksCache(LimeConfig(base_url=base))
    keys, issuer = cache.get_jwks("test-kid")
    assert issuer == "https://lime.pics"
    assert keys
    cache.close()


def test_jwks_cache_unavailable_after_kid_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = JwksCache(LimeConfig(base_url="https://lime.pics", min_refresh_seconds=0))
    snap = JwksSnapshot(
        keys=[{"kid": "present"}],
        issuer="https://lime.pics",
        fetched_at=time.monotonic(),
    )
    cache._snapshot = snap
    calls = {"count": 0}

    def current() -> JwksSnapshot | None:
        calls["count"] += 1
        return snap if calls["count"] == 1 else None

    monkeypatch.setattr(cache, "_current_snapshot", current)
    monkeypatch.setattr(cache, "refresh", lambda **_: None)
    with pytest.raises(RuntimeError, match="kid refresh"):
        cache.get_jwks("missing")
    cache.close()


@respx.mock
def test_jwks_cache_metadata_missing_jwks_uri(rsa_keypair: tuple) -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        json={"issuer": "https://lime.pics", "jwks_uri": ""},
    )
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="metadata missing jwks_uri"):
        cache.get_jwks("test-kid")
    cache.close()


@respx.mock
def test_jwks_cache_metadata_lime_envelope_rejected() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(
        json={
            "ok": True,
            "data": {
                "issuer": "https://lime.pics",
                "jwks_uri": f"https://lime.pics{JWKS_PATH}",
            },
        },
    )
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(ValueError, match="metadata missing issuer"):
        cache.refresh(force=True)
    cache.close()


@respx.mock
def test_token_verifier_invalid_token_claim(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})

    token = sign_mcp_token(private_key, extra_claims={"user_id": "forbidden"})
    verifier = TokenVerifier(base_url=base)
    result = verifier.verify(token)
    assert result.is_valid is False
    assert result.error is not None
    assert "Invalid token" in result.error
    verifier.close()


def test_jwks_cache_kid_mismatch_refresh_error_recovered(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    snap = JwksSnapshot(
        keys=[{"kid": "old"}],
        issuer="https://lime.pics",
        fetched_at=time.monotonic(),
    )
    cache = JwksCache(LimeConfig(base_url=base, min_refresh_seconds=0))
    cache._snapshot = snap

    def refresh(**_kwargs: object) -> None:
        snap.keys.append(jwk)
        raise RuntimeError("transient")

    cache.refresh = refresh  # type: ignore[method-assign]
    keys, issuer = cache.get_jwks("test-kid")
    assert issuer == "https://lime.pics"
    assert any(key.get("kid") == "test-kid" for key in keys)
    cache.close()


def test_jwks_cache_unavailable_after_initial_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = JwksCache(LimeConfig(base_url="https://lime.pics"))
    monkeypatch.setattr(cache, "refresh", lambda **_: None)
    with pytest.raises(RuntimeError, match="unavailable after refresh"):
        cache.get_jwks(None)
    cache.close()


@respx.mock
def test_token_verifier_verify_claims_raises(
    monkeypatch: pytest.MonkeyPatch,
    rsa_keypair: tuple,
) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})

    token = sign_mcp_token(private_key)
    verifier = TokenVerifier(base_url=base)

    def boom(**_kwargs: object) -> dict[str, str]:
        raise RuntimeError("decode failed")

    monkeypatch.setattr("lime_mcp_server._verifier.verify_mcp_access_token", boom)
    result = verifier.verify(token)
    assert result.is_valid is False
    assert "Verification error" in (result.error or "")
    verifier.close()


@respx.mock
def test_jwks_cache_kid_refresh_still_missing_raises(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})

    cache = JwksCache(LimeConfig(base_url=base, min_refresh_seconds=0))
    cache.get_jwks("test-kid")
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=503)
    with pytest.raises(RuntimeError):
        cache.get_jwks("missing-kid")
    cache.close()


@respx.mock
def test_jwks_cache_refresh_returns_none_snapshot() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=503)
    cache = JwksCache(LimeConfig(base_url=base))
    with pytest.raises(RuntimeError):
        cache.get_jwks(None)
    cache.close()


@respx.mock
def test_token_verifier_invalid_issuer(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})

    token = sign_mcp_token(private_key, issuer="https://wrong.example")
    verifier = TokenVerifier(base_url=base)
    result = verifier.verify(token)
    assert result.is_valid is False
    assert result.error == "Invalid issuer"
    verifier.close()


def test_token_validation_result_empty_sub_on_valid() -> None:
    result = TokenValidationResult(is_valid=True, claims={"sub": "  "})
    assert result.agent_id is None
