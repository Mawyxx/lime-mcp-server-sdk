# lime-mcp-server-sdk

Official Python SDK for **LIME MCP resource servers**. Verify short-lived MCP OAuth JWTs
(`aud=mcp`) against LIME Core JWKS — no introspection round-trip, no custom crypto.

[![PyPI](https://img.shields.io/pypi/v/lime-mcp-server-sdk)](https://pypi.org/project/lime-mcp-server-sdk/)
[![Documentation](https://readthedocs.org/projects/lime-mcp-server-sdk/badge/?version=latest)](https://lime-mcp-server-sdk.readthedocs.io/)
[![GitHub](https://img.shields.io/github/stars/Mawyxx/lime-mcp-server-sdk?style=social)](https://github.com/Mawyxx/lime-mcp-server-sdk)

## Key features

- RS256 JWT verification via cached Core JWKS
- Sync `verify()` and async `verify_async()` for ASGI servers
- Raw RFC 8414 OAuth metadata + LIME JWKS envelope handling built in
- Typed `TokenValidationResult` with `agent_id` alias for `sub`
- Framework-agnostic — use with FastMCP, Starlette, or plain middleware

## Credential boundary

| Role | Credential | SDK |
|------|------------|-----|
| Site backend | `X-Site-Token` + site passport JWT | [lime-sites-sdk](https://lime-sites-sdk.readthedocs.io/) |
| Agent worker | `X-Agent-Token` + auto MCP JWT | [lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/) |
| **MCP resource server** | **Verify Bearer MCP JWT** | **This package** |

This SDK **does not issue tokens**. Agents obtain MCP JWTs via
[`lime-agents-sdk`](https://lime-agents-sdk.readthedocs.io/).

## Platform documentation

HTTP contracts and integration guides live on the LIME platform:

- [LIME platform docs — MCP Server SDK](https://lime.pics/docs#guide-mcpServerSdk)
- [LIME platform docs — OAuth for MCP](https://lime.pics/docs#guide-oauthMcp)

## Minimal example

```python
from lime_mcp_server import TokenVerifier

verifier = TokenVerifier()  # LIME_BASE_URL, LIME_OAUTH_AUDIENCE from env
result = verifier.verify(bearer_token)
if result.is_valid:
    print(result.agent_id)  # agent UUID from claims["sub"]
```

## Next steps

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [API Reference](api.md)
- [Examples](examples.md)
