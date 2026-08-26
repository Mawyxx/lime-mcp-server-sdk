# Changelog

## Unreleased

### Docs / DX

- README leads with task + 10-second `TokenVerifier` sample; flow table below Quick start.
- Added `examples/verify-middleware` and `examples/async-warmup`.
- PyPI description: zero JWKS boilerplate.

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
