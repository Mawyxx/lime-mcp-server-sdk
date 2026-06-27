from __future__ import annotations

import pytest

from lime_mcp_server import LimeConfig, jwks_cache_ttl_seconds


def test_lime_config_defaults() -> None:
    config = LimeConfig()
    assert config.base_url == "https://lime.pics"
    assert config.audience == "mcp"
    assert config.cache_ttl == 3600
    assert config.leeway_seconds == 120
    assert config.min_refresh_seconds == 60
    assert config.allowed_algorithms == ("RS256",)


def test_lime_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIME_BASE_URL", "https://custom.example")
    monkeypatch.setenv("LIME_OAUTH_AUDIENCE", "custom-aud")
    monkeypatch.setenv("LIME_JWKS_CACHE_TTL_SECONDS", "120")
    config = LimeConfig()
    assert config.base_url == "https://custom.example"
    assert config.audience == "custom-aud"
    assert config.cache_ttl == 120


def test_jwks_cache_ttl_seconds_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIME_JWKS_CACHE_TTL_SECONDS", raising=False)
    assert jwks_cache_ttl_seconds() == 3600


def test_jwks_cache_ttl_seconds_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIME_JWKS_CACHE_TTL_SECONDS", "600")
    assert jwks_cache_ttl_seconds() == 600


def test_lime_config_strips_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIME_BASE_URL", "https://lime.pics/")
    assert LimeConfig().base_url == "https://lime.pics"
