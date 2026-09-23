from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from termix_mcp.tools.tools_files import register_files_tools

pytestmark = pytest.mark.usefixtures("patch_ssh_session")


async def test_list_files_happy_path(build_mcp, mock_client) -> None:
    mock_client.file_manager.list_files = AsyncMock(
        return_value={"path": "/", "files": [{"name": "a.txt"}]}
    )
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    result = await mcp.call_tool("termix_list_files", {"host_id": "1"})
    assert result.structured_content["path"] == "/"
    mock_client.file_manager.list_files.assert_awaited_once_with(path="/")


async def test_read_file_truncates_content(build_mcp, mock_client) -> None:
    mock_client.file_manager.read_file = AsyncMock(return_value={"content": "x" * 50})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    result = await mcp.call_tool(
        "termix_read_file", {"host_id": "1", "path": "/a.txt", "max_chars": 10}
    )
    assert result.structured_content["content"] == "x" * 10
    assert result.structured_content["content_truncated"] is True
    assert result.structured_content["content_total_chars"] == 50


async def test_read_file_no_truncation_needed(build_mcp, mock_client) -> None:
    mock_client.file_manager.read_file = AsyncMock(return_value={"content": "short"})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    result = await mcp.call_tool("termix_read_file", {"host_id": "1", "path": "/a.txt"})
    assert result.structured_content["content"] == "short"
    assert "content_truncated" not in result.structured_content


async def test_write_file_happy_path(build_mcp, mock_client) -> None:
    mock_client.file_manager.write_file = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    await mcp.call_tool("termix_write_file", {"host_id": "1", "path": "/a.txt", "content": "hello"})
    mock_client.file_manager.write_file.assert_awaited_once_with(path="/a.txt", content="hello")


async def test_create_folder_happy_path(build_mcp, mock_client) -> None:
    mock_client.file_manager.create_folder = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    await mcp.call_tool(
        "termix_create_folder", {"host_id": "1", "path": "/", "folder_name": "logs"}
    )
    mock_client.file_manager.create_folder.assert_awaited_once_with(path="/", folderName="logs")


async def test_move_file_happy_path(build_mcp, mock_client) -> None:
    mock_client.file_manager.move_item = AsyncMock(return_value={"message": "moved"})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    await mcp.call_tool(
        "termix_move_file", {"host_id": "1", "old_path": "/a.txt", "new_path": "/b/a.txt"}
    )
    mock_client.file_manager.move_item.assert_awaited_once_with(
        oldPath="/a.txt", newPath="/b/a.txt"
    )


async def test_rename_file_happy_path(build_mcp, mock_client) -> None:
    mock_client.file_manager.rename_item = AsyncMock(return_value={"message": "renamed"})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    await mcp.call_tool(
        "termix_rename_file", {"host_id": "1", "old_path": "/a.txt", "new_name": "b.txt"}
    )
    mock_client.file_manager.rename_item.assert_awaited_once_with(oldPath="/a.txt", newName="b.txt")


async def test_delete_file_defaults_to_trash(build_mcp, mock_client) -> None:
    mock_client.file_manager.delete_item = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_files_tools, TERMIX_MCP_TOOLSETS="files")

    await mcp.call_tool("termix_delete_file", {"host_id": "1", "path": "/a.txt"})
    mock_client.file_manager.delete_item.assert_awaited_once_with(
        path="/a.txt", isDirectory=False, permanent=False
    )


async def test_write_tools_absent_in_read_only_mode(build_mcp) -> None:
    mcp, _ = build_mcp(
        register_files_tools, TERMIX_MCP_TOOLSETS="files", TERMIX_MCP_READ_ONLY="true"
    )

    assert await mcp.get_tool("termix_list_files") is not None
    assert await mcp.get_tool("termix_write_file") is None
    assert await mcp.get_tool("termix_delete_file") is None
