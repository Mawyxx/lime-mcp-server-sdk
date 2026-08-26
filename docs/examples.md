# Examples

## FastMCP lifespan guard

Use `TokenVerifier` in your MCP server startup to warm JWKS before accepting traffic:

```python
from contextlib import asynccontextmanager

from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="autonomad.ai")

@asynccontextmanager
async def lifespan(_app):
    verifier.warmup()
    yield
    verifier.close()
```

For a full FastMCP + Bearer guard reference, see the LIME monorepo harness
[`scripts/verify/lime_mcp_rs_auth.py`](https://github.com/Mawyxx/Lime/blob/main/scripts/verify/lime_mcp_rs_auth.py)
(not shipped in this wheel).

## JWKS cache warmup and refresh

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="autonomad.ai")
verifier.warmup(raise_on_failure=True)

# After key rotation or repeated 401s from stale keys:
verifier.refresh_cache()
```

## Invalid and expired tokens

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="autonomad.ai")

garbage = verifier.verify("not-a-jwt")
assert garbage.is_valid is False
# error is typically "Invalid token: ..." — not "Token expired"

# "Token expired" only for a real JWT whose exp is past (and within leeway):
# expired = verifier.verify(real_expired_jwt)
# assert expired.error == "Token expired"
```

## Domain binding errors

```python
# JWT minted for another RS → Domain mismatch
result = verifier.verify(token_for_other_host)
assert result.error == "Domain mismatch"
```

## Anti-patterns

| Mistake | Correct approach |
|---------|------------------|
| `TokenVerifier()` with no pin | Pass `expected_domain=` or set `LIME_EXPECTED_DOMAIN` |
| Expect `user_id` in MCP JWT | Identity is `sub` only; use `result.agent_id` |
| Pin `host:port` | Ports are rejected — pin hostname only |
| Verify site passport with this SDK | Use `lime-sites-sdk` for `aud=lime-site-login` |
| Unwrap OAuth metadata with `{ok,data}` | Metadata is raw RFC 8414; unwrap JWKS only |
| Use `LIME_API_BASE` here | Use `LIME_BASE_URL` (origin without `/api/v1`) |
