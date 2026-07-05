# API Reference

Each method has its **own section** below. This SDK **verifies** MCP JWTs — it does not issue them.
Agents get tokens via [lime-agents-sdk](https://lime-agents-sdk.readthedocs.io/).

HTTP details: [LIME platform docs](https://lime.pics/docs#guide-mcpServerSdk).

---

## `TokenVerifier` — method index

| Method | What it does | Returns |
|--------|--------------|---------|
| [`TokenVerifier()`](#tokenverifier) | Create verifier; prefetch JWKS | `TokenVerifier` |
| [`verify()`](#verify) | Verify JWT (sync, blocks thread) | `TokenValidationResult` |
| [`verify_async()`](#verify_async) | Verify JWT (async wrapper) | `TokenValidationResult` |
| [`warmup()`](#warmup) | Prefetch metadata + JWKS | `bool` |
| [`refresh_cache()`](#refresh_cache) | Force JWKS refresh | `None` |
| [`invalidate_cache()`](#invalidate_cache) | Drop cached JWKS | `None` |
| [`close()`](#close) | Release HTTP resources | `None` |

!!! tip "Typical flow"
    `verifier = TokenVerifier()` → `result = verifier.verify(bearer_jwt)` →
    if `result.is_valid`: use `result.agent_id` (alias for JWT `sub`).

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
