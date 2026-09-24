"""MCP domain normalization for RS expected pin + JWT claim checks.

Keep the algorithm in sync with ADR 0081 / monorepo
``srcN/modules/oauth/domain/mcp_domain.py`` (reject ports — do not strip).
"""

from __future__ import annotations

import ipaddress
import re

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)

_RESERVED_EXACT = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata",
        "kubernetes",
        "kubernetes.default",
        "kubernetes.default.svc",
    }
)

_RESERVED_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".intranet",
    ".corp",
    ".home",
    ".lan",
)


def _is_reserved_hostname(host: str) -> bool:
    if host in _RESERVED_EXACT:
        return True
    return any(host.endswith(suffix) for suffix in _RESERVED_SUFFIXES)


def normalize_mcp_domain(raw: str) -> str:
    """Normalize MCP RS domain for JWT claim ``domain`` (ADR 0081 Amendment v9).

    Accepts bare hostnames or URL-ish strings. Strips ``http(s)://`` and path
    after the first ``/``. Rejects empty input, userinfo, ports, IP literals,
    and reserved/special-use hostnames (localhost, ``*.local``, cloud metadata, …).

    Raises:
        ValueError: When input is empty, a reserved hostname, or not a valid
            DNS hostname.
    """
    if not isinstance(raw, str):
        raise ValueError("domain is required")

    value = raw.strip()
    if not value:
        raise ValueError("domain is required")

    lower = value.lower()
    if lower.startswith("https://"):
        value = value[8:]
    elif lower.startswith("http://"):
        value = value[7:]

    if "/" in value:
        value = value.split("/", 1)[0]

    value = value.strip().lower()
    if not value:
        raise ValueError("domain must be a valid DNS hostname")

    if "@" in value:
        raise ValueError("domain must not include userinfo")

    if value.startswith("[") and "]" in value:
        raise ValueError("domain must not be an IP address")

    if ":" in value:
        raise ValueError("domain must not include a port")

    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ValueError("domain must not be an IP address")

    if not _HOSTNAME_RE.match(value):
        raise ValueError("domain must be a valid DNS hostname")

    if _is_reserved_hostname(value):
        raise ValueError("domain must not be a reserved or special-use hostname")

    return value
