from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError

from termix_mcp.tools.tools_users import register_users_tools


async def test_list_users_happy_path(build_mcp, mock_client) -> None:
    mock_client.user_admin.list = AsyncMock(
        return_value={"users": [{"id": "1", "username": "alice"}], "total": 1}
    )
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    result = await mcp.call_tool("termix_list_users", {})
    assert result.structured_content["items"][0]["username"] == "alice"


async def test_get_user_found(build_mcp, mock_client) -> None:
    mock_client.user_admin.list = AsyncMock(
        return_value={"users": [{"id": "1", "username": "alice"}, {"id": "2", "username": "bob"}]}
    )
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    result = await mcp.call_tool("termix_get_user", {"user_id": "2"})
    assert result.structured_content["username"] == "bob"


async def test_get_user_not_found(build_mcp, mock_client) -> None:
    mock_client.user_admin.list = AsyncMock(return_value={"users": []})
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    with pytest.raises(ToolError, match="nao encontrado"):
        await mcp.call_tool("termix_get_user", {"user_id": "999"})


async def test_list_roles_happy_path(build_mcp, mock_client) -> None:
    mock_client.rbac.list_roles = AsyncMock(return_value={"roles": [{"id": "1", "name": "admin"}]})
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    result = await mcp.call_tool("termix_list_roles", {})
    assert result.structured_content["items"][0]["name"] == "admin"


async def test_assign_role_happy_path(build_mcp, mock_client) -> None:
    mock_client.rbac.assign_role = AsyncMock(return_value={"success": True, "message": "ok"})
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    await mcp.call_tool("termix_assign_role", {"user_id": "1", "role_id": 2})
    mock_client.rbac.assign_role.assert_awaited_once_with("1", roleId=2)


async def test_list_credential_access_happy_path(build_mcp, mock_client) -> None:
    mock_client.rbac.list_credential_access = AsyncMock(
        return_value={"access": [{"userId": "1", "level": "view"}]}
    )
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    result = await mcp.call_tool("termix_list_credential_access", {"credential_id": "1"})
    assert result.structured_content["items"][0]["level"] == "view"


async def test_list_folder_access_happy_path(build_mcp, mock_client) -> None:
    mock_client.rbac.list_folder_access = AsyncMock(
        return_value={"rules": [{"folder": "prod", "userId": "1"}]}
    )
    mcp, _ = build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")

    result = await mcp.call_tool("termix_list_folder_access", {"folder": "prod"})
    assert result.structured_content["items"][0]["folder"] == "prod"
    mock_client.rbac.list_folder_access.assert_awaited_once_with(folder="prod")


async def test_all_users_tools_flagged_admin(build_mcp) -> None:
    from termix_mcp.tools.toolsets import TOOL_TABLE

    build_mcp(register_users_tools, TERMIX_MCP_TOOLSETS="users")
    assert len(TOOL_TABLE) == 6
    assert all("admin" in meta.flags for meta in TOOL_TABLE.values())
