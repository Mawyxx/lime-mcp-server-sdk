# Quick Start

One job: **verify** the Bearer JWT on incoming MCP requests. Token issuance is handled by
[lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/) on the agent side.

---

## Method order

| Step | Method | When |
|------|--------|------|
| 1 (once at startup) | `TokenVerifier()` | Process boot |
| 2 (optional) | `verifier.warmup()` | Avoid cold-start latency |
| 3 (every request) | `verifier.verify(token)` or `verify_async(token)` | Before running tool logic |
| 4 (shutdown) | `verifier.close()` | Process exit |

---

## Sync verification

Use in WSGI, scripts, or middleware that runs in a thread pool:

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

---

## Async verification (FastAPI / ASGI)

```python
result = await verifier.verify_async(token)
if result.is_valid:
    agent_id = result.agent_id
else:
    # return HTTP 401
    ...
```

---

## What `verify()` returns

Never raises for bad tokens — always check `is_valid`:

```python
result = verifier.verify(token)

result.is_valid   # True / False
result.agent_id   # agent UUID when valid (alias for claims["sub"])
result.error      # "Token expired", "Invalid audience", etc. when invalid
result.claims     # full JWT payload when valid
```

---

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `LIME_BASE_URL` | `https://lime.pics` | LIME origin (**without** `/api/v1`) |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` claim |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | How long to cache signing keys |

!!! note "Not the same as agent/site SDKs"
    Agent and site SDKs use `LIME_API_BASE` (`…/api/v1`). **This package uses
    `LIME_BASE_URL`** (origin only) because JWKS paths are resolved from the issuer root.

---

## Warm up at startup

```python
verifier = TokenVerifier()
verifier.warmup()  # non-fatal if network fails
```

---

## What this SDK does not do

| Task | Use instead |
|------|-------------|
| Agent calls MCP tools | [lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/) |
| User login on a website | [lime-sites-sdk](https://lime-sites-sdk.readthedocs.io/) |
| Issue MCP JWT | LIME platform (automatic via agents SDK) |

HTTP reference: [lime.pics/docs](https://lime.pics/docs)
