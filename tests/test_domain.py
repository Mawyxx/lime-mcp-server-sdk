from __future__ import annotations

import pytest

from lime_mcp_server import normalize_mcp_domain

# Parity with Core: keep in sync with
# testsN/modules/oauth/unit/test_mcp_domain.py (ADR 0081 Amendment v9).
_SERVER_ACCEPTS = (
    ("rs.example", "rs.example"),
    ("RS.Example", "rs.example"),
    ("https://RS.Example/path", "rs.example"),
    ("http://autonomad.ai/", "autonomad.ai"),
    ("https://sub.autonomad.ai/foo/bar", "sub.autonomad.ai"),
    ("  rs.example  ", "rs.example"),
)

_SERVER_REJECTS = (
    "",
    "   ",
    "rs.example:443",
    "127.0.0.1",
    "::1",
    "[::1]",
    "user@rs.example",
    "not a host",
    "-bad.example",
    "http://",
    "localhost",
    "foo.localhost",
    "svc.local",
    "db.internal",
    "metadata.google.internal",
)


@pytest.mark.parametrize(("raw", "expected"), _SERVER_ACCEPTS)
def test_normalize_mcp_domain_accepts_server_parity(raw: str, expected: str) -> None:
    assert normalize_mcp_domain(raw) == expected


@pytest.mark.parametrize("raw", _SERVER_REJECTS)
def test_normalize_mcp_domain_rejects_server_parity(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_mcp_domain(raw)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("", "domain is required"),
        ("   ", "domain is required"),
        ("rs.example:443", "domain must not include a port"),
        ("127.0.0.1", "domain must not be an IP address"),
        # Bare IPv6 hits the port check first (same order as Core mcp_domain.py).
        ("::1", "domain must not include a port"),
        ("[::1]", "domain must not be an IP address"),
        ("user@rs.example", "domain must not include userinfo"),
        ("not a host", "domain must be a valid DNS hostname"),
        ("-bad.example", "domain must be a valid DNS hostname"),
        ("http://", "domain must be a valid DNS hostname"),
        ("localhost", "domain must not be a reserved or special-use hostname"),
        ("foo.localhost", "domain must not be a reserved or special-use hostname"),
        ("svc.local", "domain must not be a reserved or special-use hostname"),
        ("db.internal", "domain must not be a reserved or special-use hostname"),
        (
            "metadata.google.internal",
            "domain must not be a reserved or special-use hostname",
        ),
        ("kubernetes.default.svc", "domain must not be a reserved or special-use hostname"),
    ],
)
def test_normalize_mcp_domain_reject_messages(raw: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_mcp_domain(raw)


def test_normalize_mcp_domain_non_string_required() -> None:
    with pytest.raises(ValueError, match="domain is required"):
        normalize_mcp_domain(None)  # type: ignore[arg-type]
