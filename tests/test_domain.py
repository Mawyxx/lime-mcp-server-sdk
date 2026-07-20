from __future__ import annotations

import pytest

from lime_mcp_server import normalize_mcp_domain


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("rs.example", "rs.example"),
        ("RS.Example", "rs.example"),
        ("https://RS.Example/path", "rs.example"),
        ("http://autonomad.ai/", "autonomad.ai"),
        ("https://sub.autonomad.ai/foo/bar", "sub.autonomad.ai"),
        ("  rs.example  ", "rs.example"),
        ("localhost", "localhost"),
    ],
)
def test_normalize_mcp_domain_accepts(raw: str, expected: str) -> None:
    assert normalize_mcp_domain(raw) == expected


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
    ],
)
def test_normalize_mcp_domain_rejects(raw: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_mcp_domain(raw)


def test_normalize_mcp_domain_non_string_required() -> None:
    with pytest.raises(ValueError, match="domain is required"):
        normalize_mcp_domain(None)  # type: ignore[arg-type]
