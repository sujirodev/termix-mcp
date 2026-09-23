from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from termix_mcp.tools.tools_docker import register_docker_tools

pytestmark = pytest.mark.usefixtures("patch_ssh_session")


async def test_list_containers_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.list_containers = AsyncMock(return_value=[{"id": "c1", "name": "web"}])
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool("termix_list_containers", {"host_id": "1"})
    assert result.structured_content["total"] == 1
    mock_client.docker.list_containers.assert_awaited_once_with(all="true")


async def test_list_containers_show_all_false(build_mcp, mock_client) -> None:
    mock_client.docker.list_containers = AsyncMock(return_value=[])
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    await mcp.call_tool("termix_list_containers", {"host_id": "1", "show_all": False})
    mock_client.docker.list_containers.assert_awaited_once_with(all="false")


async def test_get_container_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.get_container = AsyncMock(return_value={"id": "c1", "state": "running"})
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool("termix_get_container", {"host_id": "1", "container_id": "c1"})
    assert result.structured_content["state"] == "running"


async def test_get_container_stats_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.get_container_stats = AsyncMock(return_value={"cpu": 1.5})
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool(
        "termix_get_container_stats", {"host_id": "1", "container_id": "c1"}
    )
    assert result.structured_content["cpu"] == 1.5


async def test_get_container_logs_default_tail(build_mcp, mock_client) -> None:
    mock_client.docker.get_container_logs = AsyncMock(
        return_value={"success": True, "logs": "line1\nline2"}
    )
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    await mcp.call_tool("termix_get_container_logs", {"host_id": "1", "container_id": "c1"})
    mock_client.docker.get_container_logs.assert_awaited_once_with(
        container_id="c1", tail=200, timestamps=False
    )


async def test_start_container_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.start = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool("termix_start_container", {"host_id": "1", "container_id": "c1"})
    assert result.structured_content["success"] is True


async def test_stop_container_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.stop = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool("termix_stop_container", {"host_id": "1", "container_id": "c1"})
    assert result.structured_content["success"] is True


async def test_restart_container_happy_path(build_mcp, mock_client) -> None:
    mock_client.docker.restart = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_docker_tools, TERMIX_MCP_TOOLSETS="docker")

    result = await mcp.call_tool("termix_restart_container", {"host_id": "1", "container_id": "c1"})
    assert result.structured_content["success"] is True


async def test_write_tools_absent_in_read_only_mode(build_mcp) -> None:
    mcp, _ = build_mcp(
        register_docker_tools, TERMIX_MCP_TOOLSETS="docker", TERMIX_MCP_READ_ONLY="true"
    )

    assert await mcp.get_tool("termix_list_containers") is not None
    assert await mcp.get_tool("termix_start_container") is None
    assert await mcp.get_tool("termix_stop_container") is None
