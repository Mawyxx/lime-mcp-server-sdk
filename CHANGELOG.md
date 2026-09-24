# Changelog

## 1.0.1

### Fixed

- `normalize_mcp_domain()` rejects reserved/special-use hosts (localhost,
  `*.local`, `*.internal`, cloud metadata, `kubernetes.default.svc`) — parity
  with Core ADR 0081 Amendment v9.
- `TokenVerifier` maps unexpected verification failures through a typed error
  tuple (HTTP/OS/PyJWT) instead of bare `except Exception`; `kid` lookup no
  longer swallows non-JWT exceptions.
- Domain pin fallback through `LimeConfig()` is covered by tests; mypy strict
  assignment error in `_resolve_expected_domain` resolved.
- Tests import as a package (`tests/__init__.py`) to avoid module shadowing.

### Docs / DX

- README leads with task + 10-second `TokenVerifier` sample; flow table below Quick start.
- Added `examples/verify-middleware` and `examples/async-warmup`.
- PyPI description: zero JWKS boilerplate.
- Dropped unsupported `show_signature_defaults` mkdocstrings option so the
  strict docs build passes with mkdocstrings-python 2.x.

## 1.0.0

### BREAKING

- **`TokenVerifier` requires a domain pin.** Pass `expected_domain=` or set
  `LIME_EXPECTED_DOMAIN`. Constructing without a pin raises
  `ValueError("expected_domain is required")`.
- **JWT claim `domain` is verified** after crypto/`sub`: must be present,
  Core-canonical (no scheme/path/case drift; ports rejected), and equal the
  configured pin. Stable errors: `Missing domain claim`, `Invalid domain claim`,
  `Domain mismatch`.
- **`verify_mcp_access_token(..., expected_domain=)` is required.**

### Added

- `normalize_mcp_domain()` — public Core-aligned normalize (reject ports).
- `LimeConfig.expected_domain` / env `LIME_EXPECTED_DOMAIN`.
- `TokenValidationResult.domain` and required `McpAccessTokenClaims.domain`.

### Notes

- No dual-mode / optional domain check. Operators must pin the hostname this
  resource server serves (same profile as LIME OAuth mint).
- Port stripping is intentional **agents-sdk** behavior only; this SDK rejects
  ports like Core.

## 0.5.0

Previous release — JWKS verify without domain binding.
