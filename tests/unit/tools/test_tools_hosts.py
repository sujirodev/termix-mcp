from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError
from termix_sdk import NotFoundError

from termix_mcp.tools.tools_hosts import register_hosts_tools

HOST = {
    "id": "1",
    "name": "web1",
    "ip": "10.0.0.1",
    "folder": "prod",
    "tags": ["web", "prod"],
    "hasPassword": True,
}
HOST2 = {
    "id": "2",
    "name": "db1",
    "ip": "10.0.0.2",
    "folder": "prod",
    "tags": ["db"],
}


async def test_list_hosts_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.list = AsyncMock(return_value=[HOST, HOST2])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_hosts", {})

    assert result.structured_content["total"] == 2
    names = {item["name"] for item in result.structured_content["items"]}
    assert names == {"web1", "db1"}


async def test_list_hosts_filters_by_folder(build_mcp, mock_client) -> None:
    mock_client.hosts.list = AsyncMock(return_value=[HOST, HOST2])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_hosts", {"folder": "prod"})
    assert result.structured_content["total"] == 2

    result2 = await mcp.call_tool("termix_list_hosts", {"folder": "nope"})
    assert result2.structured_content["total"] == 0


async def test_list_hosts_filters_by_tag(build_mcp, mock_client) -> None:
    mock_client.hosts.list = AsyncMock(return_value=[HOST, HOST2])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_hosts", {"tag": "db"})
    assert [i["name"] for i in result.structured_content["items"]] == ["db1"]


async def test_list_hosts_filters_by_text(build_mcp, mock_client) -> None:
    mock_client.hosts.list = AsyncMock(return_value=[HOST, HOST2])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_hosts", {"text": "10.0.0.2"})
    assert [i["name"] for i in result.structured_content["items"]] == ["db1"]


async def test_get_host_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.retrieve = AsyncMock(return_value=HOST)
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_get_host", {"host_id": "1"})
    assert result.structured_content["name"] == "web1"


async def test_get_host_not_found_raises_tool_error(build_mcp, mock_client) -> None:
    mock_client.hosts.retrieve = AsyncMock(side_effect=NotFoundError("no such host"))
    mcp, _ = build_mcp(register_hosts_tools)

    with pytest.raises(ToolError):
        await mcp.call_tool("termix_get_host", {"host_id": "missing"})


async def test_create_host_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.create = AsyncMock(return_value=HOST)
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool(
        "termix_create_host", {"name": "web1", "ip": "10.0.0.1", "username": "root"}
    )
    assert result.structured_content["name"] == "web1"
    mock_client.hosts.create.assert_awaited_once()
    _, kwargs = mock_client.hosts.create.await_args
    assert kwargs["name"] == "web1"
    assert kwargs["port"] == 22
    assert "password" not in kwargs


async def test_update_host_merges_over_current_record(build_mcp, mock_client) -> None:
    # Termix's PUT replaces the whole row, so the tool must resend what it didn't change
    # and drop response-only fields (id, timestamps, has* flags).
    current = {**HOST, "createdAt": "2026-01-01", "hasKey": False, "enableTerminal": True}
    mock_client.hosts.retrieve = AsyncMock(return_value=current)
    mock_client.hosts.update = AsyncMock(return_value=HOST)
    mcp, _ = build_mcp(register_hosts_tools)

    await mcp.call_tool("termix_update_host", {"host_id": "1", "folder": "staging"})

    args, kwargs = mock_client.hosts.update.await_args
    assert args == ("1",)
    assert kwargs == {
        "name": "web1",
        "ip": "10.0.0.1",
        "folder": "staging",
        "tags": ["web", "prod"],
        "enableTerminal": True,
    }


async def test_delete_host_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.delete = AsyncMock(return_value={"message": "SSH host deleted"})
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_delete_host", {"host_id": "1"})
    assert result.structured_content["message"] == "SSH host deleted"


async def test_list_host_folders_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.list_folders = AsyncMock(return_value=["prod", "staging"])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_host_folders", {})
    assert result.structured_content["items"] == ["prod", "staging"]


async def test_list_host_tags_derives_unique_tags(build_mcp, mock_client) -> None:
    mock_client.hosts.list = AsyncMock(return_value=[HOST, HOST2])
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_list_host_tags", {})
    assert result.structured_content["tags"] == ["db", "prod", "web"]
    assert result.structured_content["total"] == 3


async def test_enable_host_autostart_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.enable_autostart = AsyncMock(return_value={"message": "ok", "sshConfigId": 5})
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_enable_host_autostart", {"ssh_config_id": 5})
    assert result.structured_content["sshConfigId"] == 5
    mock_client.hosts.enable_autostart.assert_awaited_once_with(sshConfigId=5)


async def test_disable_host_autostart_happy_path(build_mcp, mock_client) -> None:
    mock_client.hosts.disable_autostart = AsyncMock(
        return_value={"message": "ok", "sshConfigId": 5}
    )
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_disable_host_autostart", {"ssh_config_id": 5})
    assert result.structured_content["sshConfigId"] == 5


async def test_get_network_topology_returns_none_when_never_saved(build_mcp, mock_client) -> None:
    mock_client.network_topology.get = AsyncMock(return_value=None)
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_get_network_topology", {})
    assert result.structured_content == {"topology": None}


async def test_get_network_topology_happy_path(build_mcp, mock_client) -> None:
    mock_client.network_topology.get = AsyncMock(return_value={"topology": "{}"})
    mcp, _ = build_mcp(register_hosts_tools)

    result = await mcp.call_tool("termix_get_network_topology", {})
    assert result.structured_content["topology"] == "{}"


async def test_write_tools_absent_in_read_only_mode(build_mcp, mock_client) -> None:
    mcp, _ = build_mcp(register_hosts_tools, TERMIX_MCP_READ_ONLY="true")

    assert await mcp.get_tool("termix_list_hosts") is not None
    assert await mcp.get_tool("termix_create_host") is None
    assert await mcp.get_tool("termix_delete_host") is None
