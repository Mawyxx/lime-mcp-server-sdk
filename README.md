# lime-mcp-server-sdk — MCP OAuth JWT Verification (JWKS + RS256)

**`lime-mcp-server-sdk`** is the official **Python server SDK** for [LIME](https://lime.pics) **MCP resource servers** — verify **MCP OAuth** Bearer JWTs issued by LIME with **JWKS** + **RS256**, in-process caching, and zero-config defaults for production. Built for the [Anthropic MCP](https://modelcontextprotocol.io/) ecosystem: agents authenticate with [`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk); your server validates `Authorization: Bearer` tokens without hand-rolled PyJWT or metadata fetches on every request.

Use this package when you operate an **external MCP resource server** (FastMCP, custom HTTP `/mcp`, etc.). **Not** for site login passports (`aud=lime-site-login`) — use [`lime-sites-sdk`](https://github.com/Mawyxx/lime-site-sdk) on site backends.

[![PyPI version](https://img.shields.io/pypi/v/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/Mawyxx/lime-mcp-server-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Mawyxx/lime-mcp-server-sdk/actions/workflows/ci.yml)
[![MCP compatible](https://img.shields.io/badge/MCP-compatible-00C853)](https://modelcontextprotocol.io/)

**📖 Platform API docs:** [https://lime.pics/docs](https://lime.pics/docs#guide-mcpServerSdk)  
**📦 This SDK:** [github.com/Mawyxx/lime-mcp-server-sdk](https://github.com/Mawyxx/lime-mcp-server-sdk)  
**🌐 Platform:** [https://lime.pics](https://lime.pics)

---

## Why lime-mcp-server-sdk?

| Problem | SDK solution |
|---------|----------------|
| Manual JWKS fetch + PyJWT setup | `TokenVerifier()` — metadata-driven issuer + cached JWKS |
| Per-request network to LIME | In-memory **JWKS cache** (TTL, `kid` refresh, stale fallback) |
| Blocking verify in async servers | `verify_async()` via `asyncio.to_thread` |
| Framework lock-in | Core wheel only — bring your own FastMCP / Starlette middleware |

### MCP OAuth JWT flow (this SDK)

| Step | Who | What happens |
|------|-----|----------------|
| 1 | **Agent** ([`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk)) | `POST /api/v1/modules/oauth/token` with `X-Agent-Token` → MCP JWT (~5 min TTL) |
| 2 | **Agent** | Calls your MCP RS with `Authorization: Bearer <jwt>` |
| 3 | **Your server** (**this SDK**) | `TokenVerifier.verify(token)` → RS256 + `aud=mcp` + issuer |
| 4 | **Your server** | Use `result.agent_id` (`sub` claim) for authorization |

| Artifact | Audience | Verified by |
|----------|----------|-------------|
| **MCP access JWT** | External MCP resource servers | **`lime-mcp-server-sdk`** (`TokenVerifier`) |
| **Site passport JWT** | Site backends (`aud=lime-site-login`) | [`lime-sites-sdk`](https://github.com/Mawyxx/lime-site-sdk) — different token, different SDK |

> **Security:** MCP JWTs are **rejected on LIME HTTP APIs**. This SDK is for **your** MCP server only.

---

## Installation

```bash
pip install lime-mcp-server-sdk
```

Latest from GitHub:

```bash
pip install git+https://github.com/Mawyxx/lime-mcp-server-sdk.git
```

**Requirements:** Python 3.10+ · import: `lime_mcp_server` · deps: `PyJWT`, `cryptography`, `httpx`

---

## Quick start

### Scenario A — Sync verify (middleware / request handler)

**Story:** Extract the Bearer token from an incoming MCP request and verify it before executing tools.

```python
from lime_mcp_server import TokenVerifier, McpAccessTokenClaims

verifier = TokenVerifier()  # LIME_BASE_URL=https://lime.pics, LIME_OAUTH_AUDIENCE=mcp


def authorize_mcp_request(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    token = authorization_header.removeprefix("Bearer ").strip()
    result = verifier.verify(token)
    if not result.is_valid:
        return None
    claims: McpAccessTokenClaims = result.valid_claims  # type: ignore[assignment]
    return result.agent_id  # alias for claims["sub"] — agent UUID
```

MCP OAuth identity is claim **`sub`** (UUID). There is no separate `agent_id` JWT claim.

---

### Scenario B — Async FastMCP + JWKS warmup (production)

**Story:** Warm JWKS at startup so verification stays fast; use async verify in your MCP auth hook.

```python
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()
mcp = FastMCP("my-tools")


@asynccontextmanager
async def lifespan(app):
    if not verifier.warmup(raise_on_failure=True):
        raise RuntimeError("JWKS warmup failed")
    yield


async def verify_bearer(authorization: str) -> str | None:
    token = authorization.removeprefix("Bearer ").strip()
    result = await verifier.verify_async(token)
    return result.agent_id if result.is_valid else None


# Wire verify_bearer into your MCP server's auth layer.
# Monorepo reference: github.com/Mawyxx/Lime — scripts/verify/lime_mcp_rs_auth.py
```

`JwksCache.fetch_count` tracks successful metadata + JWKS network fetches (ops/debug).

---

## Features

- **`TokenVerifier`** — single entry point for MCP Bearer JWT validation
- **JWKS caching** — TTL (default 3600s), `kid`-mismatch refresh, min refresh interval, stale fallback on network errors
- **Fast path after warmup** — verify uses cached keys; no metadata round-trip per request
- **RS256** — PyJWT + `cryptography`; rejects forbidden site-login claims (`user_id`, `request_id`, …)
- **`verify_async()`** — non-blocking verify for ASGI / FastMCP
- **`warmup()`** — prefetch OAuth metadata (RFC 8414) + Core JWKS at startup
- **Typed claims** — `McpAccessTokenClaims` TypedDict, `py.typed`, mypy strict

---

## API reference (summary)

### `TokenVerifier`

| Method / property | Description |
|-----------------|-------------|
| `verify(token)` | Sync RS256 verify → `TokenValidationResult` |
| `await verify_async(token)` | Same, non-blocking |
| `warmup(raise_on_failure=False)` | Prefetch metadata + JWKS |
| `refresh_cache()` / `invalidate_cache()` | Force refresh or clear cache |
| `.cache` | `JwksCache` (incl. `fetch_count`) |
| `.config` | Resolved `LimeConfig` |

### `TokenValidationResult`

| Field / property | Description |
|------------------|-------------|
| `is_valid` | `True` when signature + `iss` + `aud` + `exp` pass |
| `valid_claims` | `McpAccessTokenClaims` when valid (`sub`, `iss`, `aud`, `iat`, `exp`, `jti`) |
| `agent_id` | Alias for `claims["sub"]` |
| `error` | Human-readable reason when invalid |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIME_BASE_URL` | `https://lime.pics` | LIME origin for OAuth metadata + JWKS |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | Metadata + JWKS cache TTL |
| `LIME_JWT_VERIFY_LEEWAY_SECONDS` | `120` | Clock skew leeway |
| `LIME_JWKS_MIN_REFRESH_SECONDS` | `60` | Min interval between forced JWKS refresh |

Low-level helpers (tests / advanced): `verify_mcp_access_token`, `JwksCache`, `unwrap_lime_data`, `FORBIDDEN_MCP_CLAIMS`.

---

## Related packages

| Package | Role |
|---------|------|
| [`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk) | Agent worker: issue MCP JWT + MCP client (`list_tools`, `call_tool`) |
| [`lime-sites-sdk`](https://github.com/Mawyxx/lime-site-sdk) | Site backend: site passport JWT via SSE (not MCP tokens) |

---

## Contributing

Issues and pull requests: [github.com/Mawyxx/lime-mcp-server-sdk](https://github.com/Mawyxx/lime-mcp-server-sdk)

```bash
git clone https://github.com/Mawyxx/lime-mcp-server-sdk.git
cd lime-mcp-server-sdk
pip install -e ".[dev]"
ruff check src tests
mypy src/lime_mcp_server
pytest --cov=lime_mcp_server --cov-fail-under=100
```

CI runs on Python 3.10–3.13 with **100% line coverage** on `src/lime_mcp_server`.

Live integration (optional):

```bash
LIME_MCP_SERVER_INTEGRATION=1 LIME_AGENT_TOKEN=at_... pytest tests/integration/ -v
```

---

## License

MIT — see [LICENSE](LICENSE).
