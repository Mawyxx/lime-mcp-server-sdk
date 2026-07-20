# Quick Start

Verify Bearer JWT on each MCP request. Token issuance is
[lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/).

**1.0.0:** a domain pin is mandatory (`expected_domain=` or `LIME_EXPECTED_DOMAIN`).

## Method order

| Step | Method | When |
|------|--------|------|
| 1 | `TokenVerifier(expected_domain=…)` | Process startup |
| 2 | `warmup()` | Optional — reduce cold-start latency |
| 3 | `verify(token)` or `verify_async(token)` | Every request |
| 4 | `close()` | Process shutdown |

## Sync verification

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="autonomad.ai")

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
    domain = result.domain
else:
    # return HTTP 401
    ...
```

## What `verify()` returns

Never raises for bad tokens — check `is_valid`:

| Field | Meaning |
|-------|---------|
| `is_valid` | `True` when signature, issuer, audience, expiry, and domain OK |
| `agent_id` | Agent UUID when valid (JWT `sub`) |
| `domain` | Bound RS hostname when valid |
| `error` | Reason when invalid (`"Token expired"`, `"Domain mismatch"`, …) |
| `claims` | Full payload when valid |

Stable domain errors: `Missing domain claim`, `Invalid domain claim`, `Domain mismatch`.

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `LIME_EXPECTED_DOMAIN` | *(none — required)* | Hostname this RS serves (ports rejected) |
| `LIME_BASE_URL` | `https://lime.pics` | Origin **without** `/api/v1` |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | JWKS cache TTL |

!!! note "Different from agent/site SDKs"
    Agent and site SDKs use `LIME_API_BASE` (`…/api/v1`). **This package uses
    `LIME_BASE_URL`** (origin only).

## Warm up at startup

```python
verifier = TokenVerifier(expected_domain="autonomad.ai")
verifier.warmup()
```

HTTP reference: [lime.pics/docs](https://lime.pics/docs)
