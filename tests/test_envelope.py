from __future__ import annotations

import pytest

from lime_mcp_server import unwrap_lime_data
from lime_mcp_server._envelope import FORBIDDEN_MCP_CLAIMS


def test_unwrap_lime_data_success() -> None:
    assert unwrap_lime_data({"ok": True, "data": {"keys": []}}) == {"keys": []}


def test_unwrap_lime_data_not_ok() -> None:
    with pytest.raises(ValueError, match="envelope not ok"):
        unwrap_lime_data({"ok": False, "data": {}})


def test_unwrap_lime_data_missing_data() -> None:
    with pytest.raises(ValueError, match="missing data"):
        unwrap_lime_data({"ok": True, "data": "bad"})


def test_forbidden_claims_frozen() -> None:
    assert "user_id" in FORBIDDEN_MCP_CLAIMS
