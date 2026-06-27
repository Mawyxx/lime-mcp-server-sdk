from __future__ import annotations

import jwt
import pytest

from lime_mcp_server import verify_mcp_access_token
from lime_mcp_server._types import TokenValidationResult
from tests.helpers import sign_mcp_token


def test_verify_mcp_access_token_success(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key)
    claims = verify_mcp_access_token(
        token,
        issuer="https://lime.pics",
        audience="mcp",
        jwks_keys=[jwk],
    )
    assert claims["sub"] == "agent-uuid"


def test_verify_mcp_access_token_wrong_kid(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key, kid="other-kid")
    with pytest.raises(jwt.InvalidTokenError, match="no jwks key"):
        verify_mcp_access_token(
            token,
            issuer="https://lime.pics",
            audience="mcp",
            jwks_keys=[jwk],
        )


def test_verify_mcp_access_token_forbidden_claim(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key, extra_claims={"user_id": "bad"})
    with pytest.raises(jwt.InvalidTokenError, match="forbidden"):
        verify_mcp_access_token(
            token,
            issuer="https://lime.pics",
            audience="mcp",
            jwks_keys=[jwk],
        )


def test_verify_mcp_access_token_missing_sub(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key, sub="")
    with pytest.raises(jwt.InvalidTokenError, match="missing sub"):
        verify_mcp_access_token(
            token,
            issuer="https://lime.pics",
            audience="mcp",
            jwks_keys=[jwk],
        )


def test_token_validation_result_agent_id(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key, sub="uuid-123")
    claims = verify_mcp_access_token(
        token,
        issuer="https://lime.pics",
        audience="mcp",
        jwks_keys=[jwk],
    )
    result = TokenValidationResult(is_valid=True, claims=claims)
    assert result.agent_id == "uuid-123"


def test_token_validation_result_agent_id_invalid() -> None:
    result = TokenValidationResult(is_valid=False, error="bad")
    assert result.agent_id is None


def test_verify_mcp_access_token_expired(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key, exp_offset=-10)
    with pytest.raises(jwt.ExpiredSignatureError):
        verify_mcp_access_token(
            token,
            issuer="https://lime.pics",
            audience="mcp",
            jwks_keys=[jwk],
            leeway_seconds=0,
        )


def test_verify_mcp_access_token_wrong_audience(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
    token = sign_mcp_token(private_key)
    with pytest.raises(jwt.InvalidAudienceError):
        verify_mcp_access_token(
            token,
            issuer="https://lime.pics",
            audience="wrong",
            jwks_keys=[jwk],
        )
