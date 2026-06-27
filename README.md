# lime-mcp-server-sdk

JWT verification for **LIME MCP resource servers** ([ADR 0081](https://github.com/Mawyxx/LIME)).

Install:

```bash
pip install lime-mcp-server-sdk
# FastMCP adapter:
pip install "lime-mcp-server-sdk[mcp]"
```

## Quick start

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()  # defaults: https://lime.pics, aud=mcp
result = verifier.verify(bearer_token)
if result.is_valid:
    agent_uuid = result.agent_id  # alias for claims["sub"]
```

MCP OAuth JWT identity is claim **`sub`** (UUID). There is no separate `agent_id` claim.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIME_BASE_URL` | `https://lime.pics` | LIME origin for OAuth metadata + JWKS |
| `LIME_OAUTH_AUDIENCE` | `mcp` | Expected JWT `aud` |
| `LIME_JWKS_CACHE_TTL_SECONDS` | `3600` | Metadata + JWKS cache TTL |
| `LIME_JWT_VERIFY_LEEWAY_SECONDS` | `120` | Clock skew leeway |
| `LIME_JWKS_MIN_REFRESH_SECONDS` | `60` | Min interval between forced JWKS refresh |

## FastMCP

```python
from lime_mcp_server._fastmcp import LimeMcpTokenVerifier

mcp = FastMCP(..., token_verifier=LimeMcpTokenVerifier())
```

## Development

Monorepo workspace: `sdk/lime-mcp-server-sdk/` (gitignored). Standalone repo: [github.com/Mawyxx/lime-mcp-server-sdk](https://github.com/Mawyxx/lime-mcp-server-sdk).

```bash
cd sdk/lime-mcp-server-sdk
pip install -e ".[dev,mcp]"
ruff check src tests
mypy src/lime_mcp_server
pytest --cov=lime_mcp_server --cov-fail-under=100
```

Live integration (optional):

```bash
LIME_MCP_SERVER_INTEGRATION=1 LIME_AGENT_TOKEN=at_... pytest tests/integration/ -v
```

## Changelog

### 0.1.0

- Initial release: `TokenVerifier`, `TokenValidationResult`, JWKS cache, optional FastMCP adapter.
