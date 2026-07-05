# API Reference

Read [Home](index.md) for the flow diagram and method table.

HTTP routes: [LIME platform docs](https://lime.pics/docs).

## Method order

| Step | Method |
|------|--------|
| 1 | [`TokenVerifier()`](#lime_mcp_server.TokenVerifier.__init__) |
| 2 | [`verify()`](#lime_mcp_server.TokenVerifier.verify) or [`verify_async()`](#lime_mcp_server.TokenVerifier.verify_async) |
| 3 | [`close()`](#lime_mcp_server.TokenVerifier.close) |

## Class overview

::: lime_mcp_server.TokenVerifier
    options:
      heading_level: 2
      show_root_heading: true
      members: false

## Lifecycle

::: lime_mcp_server.TokenVerifier.__init__
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

::: lime_mcp_server.TokenVerifier.close
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

## Verification

::: lime_mcp_server.TokenVerifier.verify
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

Never raises for invalid tokens — check `result.is_valid` and `result.error`.

::: lime_mcp_server.TokenVerifier.verify_async
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

## JWKS cache

::: lime_mcp_server.TokenVerifier.warmup
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

::: lime_mcp_server.TokenVerifier.refresh_cache
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

::: lime_mcp_server.TokenVerifier.invalidate_cache
    options:
      heading_level: 3
      show_root_heading: true
      show_symbol_type_heading: false

## TokenValidationResult

::: lime_mcp_server.TokenValidationResult
    options:
      heading_level: 3
      show_root_heading: true

| Field / property | Meaning |
|------------------|---------|
| `is_valid` | Signature, issuer, audience, expiry OK |
| `claims` | Decoded payload when valid |
| `error` | Reason when invalid |
| `agent_id` | Agent UUID from `sub` when valid |

## Configuration

::: lime_mcp_server.LimeConfig
    options:
      heading_level: 3
      show_root_heading: true

Env: **`LIME_BASE_URL`** (origin only, no `/api/v1`).

## Advanced — JwksCache

::: lime_mcp_server.JwksCache
    options:
      heading_level: 3
      show_root_heading: true
      members:
        - warm
        - refresh
        - invalidate
        - fetch_count
        - close
