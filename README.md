# lime-mcp-server-sdk

JWT verification for **LIME MCP resource servers** ([ADR 0081](https://github.com/Mawyxx/LIME)).

Install:

```bash
pip install lime-mcp-server-sdk
```

## Quick start

```python
from lime_mcp_server import TokenVerifier, McpAccessTokenClaims

verifier = TokenVerifier()  # defaults: https://lime.pics, aud=mcp
result = verifier.verify(bearer_token)
if result.is_valid:
    claims: McpAccessTokenClaims = result.valid_claims  # sub, iss, aud, iat, exp, jti
    agent_uuid = result.agent_id  # alias for claims["sub"]
```

MCP OAuth JWT identity is claim **`sub`** (UUID). There is no separate `agent_id` claim.

## Async verify (FastMCP / ASGI)

```python
result = await verifier.verify_async(bearer_token)
```

## Warmup (ASGI lifespan)

```python
verifier = TokenVerifier()
if not verifier.warmup(raise_on_failure=True):
    raise RuntimeError("JWKS warmup failed")
```

`JwksCache.fetch_count` tracks successful metadata+JWKS network fetches (ops/debug).

## FastMCP snippet (not shipped in wheel)

```python
from lime_mcp_server import TokenVerifier
from fastmcp import FastMCP

verifier = TokenVerifier()

async def verify_token(bearer: str) -> str | None:
    token = bearer.removeprefix("Bearer ").strip()
    result = await verifier.verify_async(token)
    return result.agent_id if result.is_valid else None
```

Monorepo reference adapter: [`scripts/verify/lime_mcp_rs_auth.py`](https://github.com/Mawyxx/Lime/blob/main/scripts/verify/lime_mcp_rs_auth.py).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIME_BASE_URL` | `https://lime.pics` | LIME origin for OAuth metadata + JWKS |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | Metadata + JWKS cache TTL |
| `LIME_JWT_VERIFY_LEEWAY_SECONDS` | `120` | Clock skew leeway |
| `LIME_JWKS_MIN_REFRESH_SECONDS` | `60` | Min interval between forced JWKS refresh |

## Development

Monorepo workspace: `sdk/lime-mcp-server-sdk/` (gitignored). Standalone repo: [github.com/Mawyxx/lime-mcp-server-sdk](https://github.com/Mawyxx/lime-mcp-server-sdk).

```bash
cd sdk/lime-mcp-server-sdk
pip install -e ".[dev]"
ruff check src tests
mypy src/lime_mcp_server
pytest --cov=lime_mcp_server --cov-fail-under=100
```

Live integration (optional):

```bash
LIME_MCP_SERVER_INTEGRATION=1 LIME_AGENT_TOKEN=at_... pytest tests/integration/ -v
```

## Publish (standalone repo)

```bash
cd sdk/lime-mcp-server-sdk
git push -u origin main
git tag v0.3.0
git push origin v0.3.0
```

GitHub Actions on tag `v*` publishes to PyPI via trusted publishing (`publish.yml`, environment `pypi`).

## Changelog

### 0.3.0

- `McpAccessTokenClaims` TypedDict; `TokenValidationResult.valid_claims`
- `verify_async()` for non-blocking RS verify
- Public `TokenVerifier.warmup()`; `JwksCache.fetch_count` observability

### 0.2.0

- Remove framework adapters (`LimeMcpTokenVerifier`, `[mcp]` extra). Core-only wheel.

### 0.1.0

- Initial release: `TokenVerifier`, `TokenValidationResult`, JWKS cache.
