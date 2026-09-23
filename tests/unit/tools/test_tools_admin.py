from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_admin import register_admin_tools


async def test_get_branding_happy_path(build_mcp, mock_client) -> None:
    mock_client.instance_settings.get_branding = AsyncMock(
        return_value={"appName": "Termix", "tagline": "SSH manager", "logo": ""}
    )
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_get_branding", {})
    assert result.structured_content["appName"] == "Termix"


async def test_update_branding_only_sends_provided_fields(build_mcp, mock_client) -> None:
    mock_client.instance_settings.update_branding = AsyncMock(return_value={"appName": "New Name"})
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    await mcp.call_tool("termix_update_branding", {"app_name": "New Name"})
    mock_client.instance_settings.update_branding.assert_awaited_once_with(appName="New Name")


async def test_update_branding_all_fields(build_mcp, mock_client) -> None:
    mock_client.instance_settings.update_branding = AsyncMock(return_value={})
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    await mcp.call_tool(
        "termix_update_branding",
        {"app_name": "New Name", "tagline": "New Tagline", "logo": "https://x/logo.png"},
    )
    mock_client.instance_settings.update_branding.assert_awaited_once_with(
        appName="New Name", tagline="New Tagline", logo="https://x/logo.png"
    )


async def test_get_host_defaults_happy_path(build_mcp, mock_client) -> None:
    mock_client.instance_settings.get_host_defaults = AsyncMock(return_value={"useSocks5": False})
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_get_host_defaults", {})
    assert result.structured_content["useSocks5"] is False


async def test_get_audit_forwarding_drops_token(build_mcp, mock_client) -> None:
    mock_client.instance_settings.get_audit_forwarding = AsyncMock(
        return_value={"url": "https://logs.example.com", "hasToken": True, "token": "secret"}
    )
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_get_audit_forwarding", {})
    assert "token" not in result.structured_content
    assert result.structured_content["hasToken"] is True


async def test_get_encryption_status_happy_path(build_mcp, mock_client) -> None:
    mock_client.encryption.get_status = AsyncMock(
        return_value={"security": {"level": "high"}, "version": "v2-kek-dek"}
    )
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_get_encryption_status", {})
    assert result.structured_content["version"] == "v2-kek-dek"


async def test_list_sso_providers_happy_path(build_mcp, mock_client) -> None:
    mock_client.sso.list_providers_admin = AsyncMock(return_value=[{"id": "1", "enabled": False}])
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_list_sso_providers", {})
    assert result.structured_content["total"] == 1


async def test_get_termix_id_status_happy_path(build_mcp, mock_client) -> None:
    mock_client.termix_id.get_me = AsyncMock(
        return_value={"identity": {"handle": "matheus"}, "keys": []}
    )
    mcp, _ = build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")

    result = await mcp.call_tool("termix_get_termix_id_status", {})
    assert result.structured_content["identity"]["handle"] == "matheus"


async def test_all_admin_tools_flagged_admin(build_mcp) -> None:
    from termix_mcp.tools.toolsets import TOOL_TABLE

    build_mcp(register_admin_tools, TERMIX_MCP_TOOLSETS="admin")
    assert len(TOOL_TABLE) == 7
    assert all("admin" in meta.flags for meta in TOOL_TABLE.values())


async def test_admin_toolset_not_included_in_all(build_mcp, mock_client, make_settings) -> None:
    from fastmcp import FastMCP

    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_TOOLSETS="all")
    register_admin_tools(mcp, mock_client, settings)

    assert await mcp.get_tool("termix_get_branding") is None
