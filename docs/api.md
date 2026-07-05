# API Reference

Start with [Home](index.md) for the verify flow and `TokenVerifier` method tree.

Each method below has its **own section**. HTTP routes: [LIME platform docs](https://lime.pics/docs).

---

## Method order

| Step | Method |
|------|--------|
| 1 | `TokenVerifier()` |
| 2 | `verify()` or `verify_async()` (every request) |
| 3 | `close()` (shutdown) |

---

## Class overview

::: lime_mcp_server.TokenVerifier
    options:
      heading_level: 2
      show_root_heading: true
      members: false

---

## Lifecycle

### `TokenVerifier()`

::: lime_mcp_server.TokenVerifier.__init__
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

### `close()`

::: lime_mcp_server.TokenVerifier.close
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

---

## Verification

### `verify()`

::: lime_mcp_server.TokenVerifier.verify
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

**Never raises** for invalid tokens — check `result.is_valid` and `result.error`.

### `verify_async()`

::: lime_mcp_server.TokenVerifier.verify_async
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

---

## JWKS cache

### `warmup()`

::: lime_mcp_server.TokenVerifier.warmup
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

### `refresh_cache()`

::: lime_mcp_server.TokenVerifier.refresh_cache
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

### `invalidate_cache()`

::: lime_mcp_server.TokenVerifier.invalidate_cache
    options:
      heading_level: 4
      show_root_heading: true
      show_symbol_type_heading: false

---

## `TokenValidationResult`

::: lime_mcp_server.TokenValidationResult
    options:
      heading_level: 3
      show_root_heading: true

| Field / property | Meaning |
|------------------|---------|
| `is_valid` | `True` when signature, iss, aud, exp OK |
| `claims` | Decoded JWT payload when valid |
| `error` | Human-readable reason when invalid |
| `agent_id` | Property — agent UUID from `sub` (only when valid) |

---

## Configuration

### `LimeConfig`

::: lime_mcp_server.LimeConfig
    options:
      heading_level: 3
      show_root_heading: true

Env vars use **`LIME_BASE_URL`** (origin only, no `/api/v1`) — different from agents/sites SDK.

---

## Advanced — `JwksCache`

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
