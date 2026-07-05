# Quick Start

Verify Bearer JWT on each MCP request. Token issuance is
[lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/).

## Method order

| Step | Method | When |
|------|--------|------|
| 1 | `TokenVerifier()` | Process startup |
| 2 | `warmup()` | Optional — reduce cold-start latency |
| 3 | `verify(token)` or `verify_async(token)` | Every request |
| 4 | `close()` | Process shutdown |

## Sync verification

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()

def authenticate(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    result = verifier.verify(token)
    if result.is_valid:
        return result.agent_id
    print("Auth failed:", result.error)
    return None
```

## Async verification (FastAPI / ASGI)

```python
result = await verifier.verify_async(token)
if result.is_valid:
    agent_id = result.agent_id
else:
    # return HTTP 401
    ...
```

## What `verify()` returns

Never raises for bad tokens — check `is_valid`:

| Field | Meaning |
|-------|---------|
| `is_valid` | `True` when signature, issuer, audience, expiry OK |
| `agent_id` | Agent UUID when valid (JWT `sub`) |
| `error` | Reason when invalid (`"Token expired"`, etc.) |
| `claims` | Full payload when valid |

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `LIME_BASE_URL` | `https://lime.pics` | Origin **without** `/api/v1` |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | JWKS cache TTL |

!!! note "Different from agent/site SDKs"
    Agent and site SDKs use `LIME_API_BASE` (`…/api/v1`). **This package uses
    `LIME_BASE_URL`** (origin only).

## Warm up at startup

```python
verifier = TokenVerifier()
verifier.warmup()
```

HTTP reference: [lime.pics/docs](https://lime.pics/docs)
