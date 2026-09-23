from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_tunnels import register_tunnels_tools


async def test_list_tunnels_happy_path(build_mcp, mock_client) -> None:
    mock_client.tunnel.get_status = AsyncMock(return_value={"tunnel-a": {"status": "connected"}})
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    result = await mcp.call_tool("termix_list_tunnels", {})
    assert result.structured_content["tunnel-a"]["status"] == "connected"


async def test_get_tunnel_happy_path(build_mcp, mock_client) -> None:
    mock_client.tunnel.get_status_by_name = AsyncMock(
        return_value={"name": "tunnel-a", "status": {"connected": True}}
    )
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    result = await mcp.call_tool("termix_get_tunnel", {"tunnel_name": "tunnel-a"})
    assert result.structured_content["name"] == "tunnel-a"
    mock_client.tunnel.get_status_by_name.assert_awaited_once_with("tunnel-a")


async def test_create_tunnel_only_sends_provided_fields(build_mcp, mock_client) -> None:
    mock_client.tunnel.connect = AsyncMock(return_value={"message": "ok", "tunnelName": "t1"})
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    await mcp.call_tool(
        "termix_create_tunnel",
        {
            "name": "t1",
            "source_host_id": 5,
            "mode": "local",
            "source_port": 8080,
            "local_address": "127.0.0.1:80",
        },
    )
    mock_client.tunnel.connect.assert_awaited_once_with(
        name="t1",
        sourceHostId=5,
        mode="local",
        sourcePort=8080,
        autoStart=False,
        localAddress="127.0.0.1:80",
    )


async def test_create_tunnel_with_target_and_remote_address(build_mcp, mock_client) -> None:
    mock_client.tunnel.connect = AsyncMock(return_value={"message": "ok", "tunnelName": "t2"})
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    await mcp.call_tool(
        "termix_create_tunnel",
        {
            "name": "t2",
            "source_host_id": 5,
            "mode": "remote",
            "source_port": 2222,
            "target_host": "10.0.0.5",
            "remote_address": "10.0.0.5:22",
        },
    )
    mock_client.tunnel.connect.assert_awaited_once_with(
        name="t2",
        sourceHostId=5,
        mode="remote",
        sourcePort=2222,
        autoStart=False,
        targetHost="10.0.0.5",
        remoteAddress="10.0.0.5:22",
    )


async def test_delete_tunnel_happy_path(build_mcp, mock_client) -> None:
    mock_client.tunnel.disconnect = AsyncMock(return_value={"message": "ok", "tunnelName": "t1"})
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    await mcp.call_tool("termix_delete_tunnel", {"tunnel_name": "t1"})
    mock_client.tunnel.disconnect.assert_awaited_once_with(tunnelName="t1")


async def test_list_tunnel_presets_happy_path(build_mcp, mock_client) -> None:
    mock_client.tunnel_presets.list = AsyncMock(return_value=[{"id": "1", "name": "preset-a"}])
    mcp, _ = build_mcp(register_tunnels_tools, TERMIX_MCP_TOOLSETS="tunnels")

    result = await mcp.call_tool("termix_list_tunnel_presets", {})
    assert result.structured_content["total"] == 1
