# lime-mcp-server-sdk

Python library for **your MCP server** — the service that exposes tools/resources and must
check that the caller is a real LIME agent.

[![PyPI](https://img.shields.io/pypi/v/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![Documentation](https://readthedocs.org/projects/lime-mcp-server-sdk/badge/?version=latest)](https://lime-mcp-server-sdk.readthedocs.io/)
[![GitHub](https://img.shields.io/github/stars/Mawyxx/lime-mcp-server-sdk?style=social)](https://github.com/Mawyxx/lime-mcp-server-sdk)

---

## Who is this for?

You run an **MCP resource server** (FastMCP, custom HTTP, etc.). Agents call your server
with `Authorization: Bearer <jwt>`. This SDK answers one question:

> Is this JWT really issued by LIME, and which agent is it?

This SDK **does not**:

- Issue tokens (agents use [lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/))
- Handle website login (sites use [lime-sites-sdk](https://lime-sites-sdk.readthedocs.io/))

---

## One scenario — verify MCP Bearer token

```
Agent (lime-agents-sdk)          YOUR MCP SERVER (this SDK)
        │                                │
        │  list_tools / call_tool        │
        │  Authorization: Bearer <jwt>   │
        │───────────────────────────────>│  TokenVerifier.verify(jwt)
        │                                │  → is_valid? agent_id?
        │                                │  → run tool or return 401
```

---

## Class structure: `TokenVerifier`

```
TokenVerifier
│
├─── SETUP
│    verifier = TokenVerifier()     reads LIME_BASE_URL; prefetches JWKS
│    verifier.close()               release HTTP pool
│
├─── MAIN METHOD (call on every request)
│    result = verifier.verify(bearer_jwt)        sync — blocks thread briefly
│    result = await verifier.verify_async(jwt)   async — for FastAPI/ASGI
│
│    if result.is_valid:
│        agent_id = result.agent_id    # agent UUID (JWT "sub")
│    else:
│        error = result.error          # human-readable reason
│
└─── CACHE (optional, startup / ops)
     verifier.warmup()                prefetch keys at boot
     verifier.refresh_cache()          force refresh
     verifier.invalidate_cache()       clear cache
```

Return type details: [API Reference — TokenValidationResult](api.md#tokenvalidationresult)

---

## Minimal example

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()

def check_request(authorization_header: str) -> str | None:
    # Strip "Bearer " prefix
    token = authorization_header.removeprefix("Bearer ").strip()
    result = verifier.verify(token)
    if result.is_valid:
        return result.agent_id   # use for authorization in your tool handlers
    return None                  # → respond 401
```

---

## What you need before coding

| Item | Notes |
|------|-------|
| Public LIME instance | Default `https://lime.pics` via `LIME_BASE_URL` |
| Bearer JWT from agent | Agent gets it automatically via lime-agents-sdk MCP calls |

Env var is **`LIME_BASE_URL`** (origin only, **no** `/api/v1`) — different from agent/site SDKs.

---

## Install

```bash
pip install lime-mcp-server-sdk
```

Details: [Installation](installation.md)

---

## Other LIME SDKs

| SDK | Role |
|-----|------|
| [lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/) | Agent calls your MCP server |
| [lime-sites-sdk](https://lime-sites-sdk.readthedocs.io/) | Website login (unrelated) |
| **lime-mcp-server-sdk** (this) | You verify tokens on MCP server |

Platform HTTP reference: [lime.pics/docs](https://lime.pics/docs#guide-mcpServerSdk)

---

## Next pages

1. [Quick Start](quickstart.md) — sync/async verify, env table
2. [API Reference](api.md) — every method
3. [Examples](examples.md) — FastMCP, cache warmup, invalid token
