# Quick Start

## Verify an MCP Bearer JWT

Agents send `Authorization: Bearer <jwt>` to your MCP resource server. Verify the token
with `TokenVerifier`:

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()
result = verifier.verify(bearer_token)

if result.is_valid:
    agent_id = result.agent_id  # claims["sub"]
else:
    print(result.error)
```

## Async verification (ASGI / FastAPI)

```python
result = await verifier.verify_async(bearer_token)
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LIME_BASE_URL` | `https://lime.pics` | LIME origin (**without** `/api/v1`) |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` claim |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | JWKS cache TTL |
| `LIME_JWT_VERIFY_LEEWAY_SECONDS` | `120` | Clock skew leeway |
| `LIME_JWKS_MIN_REFRESH_SECONDS` | `60` | Minimum interval between forced JWKS refreshes |

!!! note "Different from agent/site SDKs"
    Agent and site SDKs use `LIME_API_BASE` (includes `/api/v1`). This package uses
    `LIME_BASE_URL` (origin only) because JWKS and OAuth metadata paths are resolved
    relative to the issuer.

## Warm up JWKS cache

Prefetch metadata and JWKS at process startup to avoid cold-start latency:

```python
verifier = TokenVerifier()
verifier.warmup()  # non-fatal on network failure
```

## What this SDK does not do

- Issue MCP OAuth tokens (use [`lime-agents-sdk`](https://lime-agents-sdk.readthedocs.io/))
- Verify site-login passports (`aud=lime-site-login`) — use
  [`lime-sites-sdk`](https://lime-sites-sdk.readthedocs.io/)

See [LIME platform docs](https://lime.pics/docs) for HTTP reference.
