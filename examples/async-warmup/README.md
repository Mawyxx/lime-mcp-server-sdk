# Async verify + JWKS warmup

Warm JWKS at process start, then use `verify_async` in your ASGI/FastMCP auth hook.
