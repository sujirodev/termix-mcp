from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError
from termix_sdk import NotFoundError

from termix_mcp.tools.tools_snippets import register_snippets_tools

SNIPPET = {"id": "1", "name": "restart-nginx", "content": "systemctl restart nginx"}


async def test_list_snippets_happy_path(build_mcp, mock_client) -> None:
    mock_client.snippets.list = AsyncMock(return_value=[SNIPPET])
    mcp, _ = build_mcp(register_snippets_tools)

    result = await mcp.call_tool("termix_list_snippets", {})
    assert result.structured_content["total"] == 1


async def test_get_snippet_happy_path(build_mcp, mock_client) -> None:
    mock_client.snippets.retrieve = AsyncMock(return_value=SNIPPET)
    mcp, _ = build_mcp(register_snippets_tools)

    result = await mcp.call_tool("termix_get_snippet", {"snippet_id": "1"})
    assert result.structured_content["name"] == "restart-nginx"


async def test_get_snippet_not_found(build_mcp, mock_client) -> None:
    mock_client.snippets.retrieve = AsyncMock(side_effect=NotFoundError("gone"))
    mcp, _ = build_mcp(register_snippets_tools)

    with pytest.raises(ToolError):
        await mcp.call_tool("termix_get_snippet", {"snippet_id": "x"})


async def test_create_snippet_happy_path(build_mcp, mock_client) -> None:
    mock_client.snippets.create = AsyncMock(return_value=SNIPPET)
    mcp, _ = build_mcp(register_snippets_tools)

    result = await mcp.call_tool(
        "termix_create_snippet", {"name": "restart-nginx", "content": "systemctl restart nginx"}
    )
    assert result.structured_content["id"] == "1"
    mock_client.snippets.create.assert_awaited_once_with(
        name="restart-nginx", content="systemctl restart nginx"
    )


async def test_create_snippet_includes_all_optional_fields_when_given(
    build_mcp, mock_client
) -> None:
    mock_client.snippets.create = AsyncMock(return_value=SNIPPET)
    mcp, _ = build_mcp(register_snippets_tools)

    await mcp.call_tool(
        "termix_create_snippet",
        {
            "name": "n",
            "content": "c",
            "description": "d",
            "folder": "ops",
            "host_filter": "prod-*",
        },
    )
    mock_client.snippets.create.assert_awaited_once_with(
        name="n", content="c", description="d", folder="ops", hostFilter="prod-*"
    )


async def test_update_snippet_includes_all_optional_fields_when_given(
    build_mcp, mock_client
) -> None:
    mock_client.snippets.update = AsyncMock(return_value=SNIPPET)
    mcp, _ = build_mcp(register_snippets_tools)

    await mcp.call_tool(
        "termix_update_snippet",
        {
            "snippet_id": "1",
            "name": "n",
            "content": "c",
            "description": "d",
            "folder": "ops",
            "host_filter": "prod-*",
        },
    )
    args, kwargs = mock_client.snippets.update.await_args
    assert args == ("1",)
    assert kwargs == {
        "name": "n",
        "content": "c",
        "description": "d",
        "folder": "ops",
        "hostFilter": "prod-*",
    }


async def test_update_snippet_only_sends_provided_fields(build_mcp, mock_client) -> None:
    mock_client.snippets.update = AsyncMock(return_value=SNIPPET)
    mcp, _ = build_mcp(register_snippets_tools)

    await mcp.call_tool("termix_update_snippet", {"snippet_id": "1", "folder": "ops"})

    args, kwargs = mock_client.snippets.update.await_args
    assert args == ("1",)
    assert kwargs == {"folder": "ops"}


async def test_delete_snippet_happy_path(build_mcp, mock_client) -> None:
    mock_client.snippets.delete = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_snippets_tools)

    result = await mcp.call_tool("termix_delete_snippet", {"snippet_id": "1"})
    assert result.structured_content["success"] is True


async def test_run_snippet_happy_path(build_mcp, mock_client) -> None:
    mock_client.snippets.execute = AsyncMock(
        return_value={"success": True, "output": "done", "error": ""}
    )
    mcp, _ = build_mcp(register_snippets_tools)

    result = await mcp.call_tool(
        "termix_run_snippet", {"snippet_id": 1, "host_id": 2, "input_values": {"x": "y"}}
    )
    assert result.structured_content["output"] == "done"
    mock_client.snippets.execute.assert_awaited_once_with(
        snippetId=1, hostId=2, inputValues={"x": "y"}
    )


async def test_run_snippet_defaults_empty_input_values(build_mcp, mock_client) -> None:
    mock_client.snippets.execute = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_snippets_tools)

    await mcp.call_tool("termix_run_snippet", {"snippet_id": 1, "host_id": 2})
    mock_client.snippets.execute.assert_awaited_once_with(snippetId=1, hostId=2, inputValues={})


async def test_write_tools_absent_in_read_only_mode(build_mcp) -> None:
    mcp, _ = build_mcp(register_snippets_tools, TERMIX_MCP_READ_ONLY="true")

    assert await mcp.get_tool("termix_list_snippets") is not None
    assert await mcp.get_tool("termix_run_snippet") is None
    assert await mcp.get_tool("termix_delete_snippet") is None
