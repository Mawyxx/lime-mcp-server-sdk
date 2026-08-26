# lime-mcp-server-sdk

Verify **LIME MCP passport JWTs** on your resource server — local JWKS, no LIME hop on the hot path.

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="tools.example.com")

result = verifier.verify(bearer_token)  # Authorization: Bearer <jwt>
if result.is_valid:
    agent_id = result.agent_id  # claims["sub"] — then YOUR ACL
```

**What the SDK handles:** JWKS fetch · cache · RS256 · `aud=mcp` · issuer · `domain` pin · async verify.

[![PyPI version](https://img.shields.io/pypi/v/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/Mawyxx/lime-mcp-server-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Mawyxx/lime-mcp-server-sdk/actions/workflows/ci.yml)
[![Documentation](https://readthedocs.org/projects/lime-mcp-server-sdk/badge/?version=latest)](https://lime-mcp-server-sdk.readthedocs.io/)
[![MCP compatible](https://img.shields.io/badge/MCP-compatible-00C853)](https://modelcontextprotocol.io/)

**Docs:** [Read the Docs](https://lime-mcp-server-sdk.readthedocs.io/) · [lime.pics/docs](https://lime.pics/docs#guide-mcpServerSdk) · [Platform](https://lime.pics)

---

## Installation

```bash
pip install lime-mcp-server-sdk
# pin the hostname this RS serves:
export LIME_EXPECTED_DOMAIN=tools.example.com
```

**Requirements:** Python 3.10+ · `PyJWT` · `cryptography` · `httpx`  
**Config:** `expected_domain=` or `LIME_EXPECTED_DOMAIN`. Zero JWKS boilerplate — not zero config.

---

## Quick start (canonical) — verify Bearer

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="tools.example.com")


def authorize_mcp_request(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    token = authorization_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    result = verifier.verify(token)
    if not result.is_valid:
        return None
    return result.agent_id  # then apply YOUR tool ACL
```

Copy-paste: [`examples/verify-middleware/`](examples/verify-middleware/).

**Agent side** issues the JWT with [`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk) (`list_tools` / `call_tool`). This package only **verifies**.

---

## Mental model

```text
TokenVerifier
├── verify(token) / verify_async(token)   ← primary
├── warmup()                              ← production startup
└── cache / refresh / invalidate          ← advanced
```

| Artifact | Audience | Verified here? |
|----------|----------|----------------|
| MCP JWT (`aud=mcp`) | Your MCP RS | **Yes** |
| Site passport (`aud=lime-site-login`) | Site backend | **No** — use [`lime-sites-sdk`](https://github.com/Mawyxx/lime-site-sdk) |

Never send `X-Agent-Token` to the MCP server. Agents send only `Authorization: Bearer <passport>`.

---

## Production — async + JWKS warmup

```python
from contextlib import asynccontextmanager

from lime_mcp_server import TokenVerifier

verifier = TokenVerifier(expected_domain="tools.example.com")


@asynccontextmanager
async def lifespan(app):
    verifier.warmup(raise_on_failure=True)  # raises on JWKS failure
    yield


async def verify_bearer(authorization: str) -> str | None:
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        return None
    result = await verifier.verify_async(token)
    if not result.is_valid:
        return None
    return result.agent_id
```

Example: [`examples/async-warmup/`](examples/async-warmup/).

---

## How the flow fits together

| Step | Who | What |
|------|-----|------|
| 1 | Agent ([`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk)) | Issues MCP JWT from `X-Agent-Token` |
| 2 | Agent | Calls your RS with `Authorization: Bearer <jwt>` |
| 3 | **Your server (this SDK)** | `TokenVerifier.verify` — RS256 + `aud` + `domain` |
| 4 | Your server | `agent_id = sub` → **your** ACL |

MCP JWTs are **rejected on LIME HTTP APIs**. This SDK is for **your** MCP server only.

---

## API surface (summary)

| Method | Description |
|--------|-------------|
| `verify(token)` | Sync RS256 verify → `TokenValidationResult` |
| `verify_async(token)` | Non-blocking verify |
| `warmup()` | Prefetch OAuth metadata + JWKS |
| `.cache` / `refresh_cache()` / `invalidate_cache()` | JWKS cache control |

**Result:** `is_valid`, `agent_id` (`sub`), `domain`, `error`, `valid_claims`.

**Env:** `LIME_EXPECTED_DOMAIN` (or kwarg), `LIME_BASE_URL` (default `https://lime.pics`), cache/leeway knobs — see RTD.

Full reference: [Read the Docs — API](https://lime-mcp-server-sdk.readthedocs.io/).

---

## Related packages

| Package | Role |
|---------|------|
| [`lime-agents-sdk`](https://github.com/Mawyxx/lime-agents-sdk) | Agent worker: issue MCP JWT + call tools |
| [`lime-sites-sdk`](https://github.com/Mawyxx/lime-site-sdk) | Site backend: site login / binding passports |

---

## Examples

| Path | Purpose |
|------|---------|
| [`examples/verify-middleware/`](examples/verify-middleware/) | Sync Bearer check |
| [`examples/async-warmup/`](examples/async-warmup/) | Warmup + `verify_async` |

---

## Contributing

```bash
git clone https://github.com/Mawyxx/lime-mcp-server-sdk.git
cd lime-mcp-server-sdk
pip install -e ".[dev]"
ruff check src tests
mypy src/lime_mcp_server
pytest --cov=lime_mcp_server --cov-fail-under=100
```

---

## License

MIT — see [LICENSE](LICENSE).
