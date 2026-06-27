from __future__ import annotations

import respx
import pytest

from lime_mcp_server import TokenVerifier
from lime_mcp_server._cache import JwksCache
from lime_mcp_server._config import LimeConfig
from lime_mcp_server._envelope import JWKS_PATH, METADATA_PATH
from tests.helpers import sign_mcp_token


def _metadata_body() -> dict:
    return {
        "ok": True,
        "data": {
            "issuer": "https://lime.pics",
            "jwks_uri": f"https://lime.pics{JWKS_PATH}",
        },
    }


def _jwks_body(jwk: dict) -> dict:
    return {"ok": True, "data": {"keys": [jwk]}}


@respx.mock
def test_token_verifier_success(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    token = sign_mcp_token(private_key)
    with TokenVerifier(base_url=base, cache_ttl=3600, min_refresh_seconds=0) as verifier:
        result = verifier.verify(token)
    assert result.is_valid is True
    assert result.agent_id == "agent-uuid"
    assert result.error is None


@respx.mock
def test_token_verifier_expired(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    token = sign_mcp_token(private_key, exp_offset=-3600)
    verifier = TokenVerifier(base_url=base, leeway_seconds=0)
    result = verifier.verify(token)
    assert result.is_valid is False
    assert result.error == "Token expired"
    verifier.close()


@respx.mock
def test_token_verifier_invalid_token() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": []}})

    verifier = TokenVerifier(base_url=base)
    result = verifier.verify("not-a-jwt")
    assert result.is_valid is False
    assert result.error is not None
    verifier.close()


@respx.mock
def test_token_verifier_refresh_and_invalidate(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    verifier = TokenVerifier(base_url=base, min_refresh_seconds=0)
    verifier.refresh_cache()
    verifier.invalidate_cache()
    token = sign_mcp_token(private_key)
    result = verifier.verify(token)
    assert result.is_valid is True
    verifier.close()


@respx.mock
def test_token_verifier_invalid_audience(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    token = sign_mcp_token(private_key, audience="wrong")
    verifier = TokenVerifier(base_url=base, audience="mcp")
    result = verifier.verify(token)
    assert result.is_valid is False
    assert result.error == "Invalid audience"
    verifier.close()


@respx.mock
def test_token_verifier_network_error_no_cache() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=503)
    config = LimeConfig(base_url=base)
    cache = JwksCache(config)
    verifier = TokenVerifier(config=config, cache=cache)
    result = verifier.verify("header.payload.sig")
    assert result.is_valid is False
    assert "Verification error" in (result.error or "")
    verifier.close()


def test_token_verifier_get_kid_invalid() -> None:
    assert TokenVerifier._get_kid("bad") is None


def test_token_verifier_config_property() -> None:
    verifier = TokenVerifier(base_url="https://lime.pics", audience="mcp")
    assert verifier.config.base_url == "https://lime.pics"
    assert verifier.config.audience == "mcp"
    verifier.close()


@respx.mock
def test_token_verifier_valid_claims_property(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    token = sign_mcp_token(private_key)
    verifier = TokenVerifier(base_url=base, min_refresh_seconds=0)
    result = verifier.verify(token)
    assert result.valid_claims is not None
    assert result.valid_claims["sub"] == "agent-uuid"
    assert result.valid_claims["aud"] == "mcp"
    verifier.close()


@respx.mock
def test_token_verifier_warmup_success(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, min_refresh_seconds=0)
    cache = JwksCache(config)
    verifier = TokenVerifier(config=config, cache=cache)
    assert verifier.warmup() is True
    assert verifier.cache.fetch_count >= 1
    verifier.close()


@respx.mock
def test_token_verifier_warmup_raise_on_failure_success(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    config = LimeConfig(base_url=base, min_refresh_seconds=0)
    cache = JwksCache(config)
    verifier = TokenVerifier(config=config, cache=cache)
    assert verifier.warmup(raise_on_failure=True) is True
    verifier.close()


@respx.mock
def test_token_verifier_cache_property(rsa_keypair: tuple) -> None:
    _, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    verifier = TokenVerifier(base_url=base, audience="mcp", min_refresh_seconds=0)
    assert verifier.cache is verifier._cache  # noqa: SLF001
    verifier.close()


@respx.mock
def test_token_verifier_warmup_raise_on_failure() -> None:
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(status_code=503)
    config = LimeConfig(base_url=base)
    cache = JwksCache(config)
    verifier = TokenVerifier(config=config, cache=cache)
    assert verifier.warmup(raise_on_failure=False) is False
    with pytest.raises(RuntimeError):
        verifier.warmup(raise_on_failure=True)
    verifier.close()


@respx.mock
def test_token_verifier_verify_async(rsa_keypair: tuple) -> None:
    import asyncio

    private_key, jwk = rsa_keypair
    base = "https://lime.pics"
    respx.get(f"{base}{METADATA_PATH}").respond(json=_metadata_body())
    respx.get(f"{base}{JWKS_PATH}").respond(json=_jwks_body(jwk))

    token = sign_mcp_token(private_key)
    verifier = TokenVerifier(base_url=base, min_refresh_seconds=0)
    result = asyncio.run(verifier.verify_async(token))
    assert result.is_valid is True
    assert result.agent_id == "agent-uuid"
    verifier.close()
