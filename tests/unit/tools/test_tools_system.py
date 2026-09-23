from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError
from termix_sdk import PermissionError as TermixPermissionError

from termix_mcp.tools.tools_system import register_system_tools


async def test_get_system_info_composes_health_and_version(build_mcp, mock_client) -> None:
    mock_client.system.health = AsyncMock(return_value={"status": "ok"})
    mock_client.system.version = AsyncMock(return_value={"version": "2.8.0"})
    mcp, _ = build_mcp(register_system_tools)

    result = await mcp.call_tool("termix_get_system_info", {})
    assert result.structured_content["status"] == "ok"
    assert result.structured_content["version"]["version"] == "2.8.0"


async def test_list_api_keys_never_exposes_token(build_mcp, mock_client) -> None:
    mock_client.api_keys.list = AsyncMock(
        return_value={
            "apiKeys": [
                {"id": "1", "name": "mcp-key", "tokenPrefix": "tmx_ab", "token": "tmx_abcsecret"}
            ]
        }
    )
    mcp, _ = build_mcp(register_system_tools)

    result = await mcp.call_tool("termix_list_api_keys", {})
    item = result.structured_content["items"][0]
    assert "token" not in item
    assert item["tokenPrefix"] == "tmx_ab"


async def test_list_api_keys_permission_denied(build_mcp, mock_client) -> None:
    mock_client.api_keys.list = AsyncMock(side_effect=TermixPermissionError("admin only"))
    mcp, _ = build_mcp(register_system_tools)

    with pytest.raises(ToolError, match="RBAC"):
        await mcp.call_tool("termix_list_api_keys", {})


async def test_get_preferences_redacts_secret_looking_fields(build_mcp, mock_client) -> None:
    mock_client.preferences.get_user_preferences = AsyncMock(
        return_value={"theme": "dark", "aiApiKey": "sk-secret"}
    )
    mcp, _ = build_mcp(register_system_tools)

    result = await mcp.call_tool("termix_get_preferences", {})
    assert result.structured_content["theme"] == "dark"
    assert result.structured_content["aiApiKey"] == "***"
