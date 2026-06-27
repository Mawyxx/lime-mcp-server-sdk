from __future__ import annotations

import asyncio

import respx

from lime_mcp_server._envelope import JWKS_PATH, METADATA_PATH
from lime_mcp_server._fastmcp import LimeMcpTokenVerifier
from tests.helpers import sign_mcp_token


@respx.mock
def test_lime_mcp_token_verifier_success(rsa_keypair: tuple) -> None:
    private_key, jwk = rsa_keypair
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
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": [jwk]}})

    token = sign_mcp_token(private_key)
    adapter = LimeMcpTokenVerifier(base_url=base)
    access = asyncio.run(adapter.verify_token(token))
    assert access is not None
    assert access.subject == "agent-uuid"
    adapter._verifier.close()


@respx.mock
def test_lime_mcp_token_verifier_rejects_invalid() -> None:
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
    respx.get(f"{base}{JWKS_PATH}").respond(json={"ok": True, "data": {"keys": []}})

    adapter = LimeMcpTokenVerifier(base_url=base)
    access = asyncio.run(adapter.verify_token("bad.token.here"))
    assert access is None
    adapter._verifier.close()
