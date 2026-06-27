from __future__ import annotations

import asyncio
import logging

from mcp.server.auth.provider import AccessToken

from lime_mcp_server._config import LimeConfig
from lime_mcp_server._verifier import TokenVerifier

logger = logging.getLogger("lime.mcp_server")


class LimeMcpTokenVerifier:
    """FastMCP token verifier adapter for LIME MCP JWTs."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        audience: str | None = None,
        verifier: TokenVerifier | None = None,
    ) -> None:
        self._verifier = verifier or TokenVerifier(base_url=base_url, audience=audience)
        self._base_url = self._verifier.config.base_url
        self._audience = self._verifier.config.audience

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            result = await asyncio.to_thread(self._verifier.verify, token)
        except Exception:
            logger.debug("MCP JWT verification failed", exc_info=True)
            return None

        if not result.is_valid or result.claims is None:
            logger.debug("MCP JWT rejected: %s", result.error)
            return None

        subject = str(result.claims["sub"])
        logger.info("MCP JWT accepted sub=%s", subject)
        return AccessToken(
            token=token,
            client_id=subject,
            scopes=[],
            subject=subject,
            claims=dict(result.claims),
        )


def default_lime_config() -> LimeConfig:
    return LimeConfig()
