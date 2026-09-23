from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_audit import register_audit_tools


async def test_list_audit_events_stringifies_page_and_limit(build_mcp, mock_client) -> None:
    mock_client.audit.list = AsyncMock(
        return_value={"logs": [], "total": 0, "page": "1", "totalPages": "1"}
    )
    mcp, _ = build_mcp(register_audit_tools)

    await mcp.call_tool("termix_list_audit_events", {"page": 2, "limit": 10})
    mock_client.audit.list.assert_awaited_once_with(page="2", limit="10")


async def test_list_session_logs_happy_path(build_mcp, mock_client) -> None:
    mock_client.session_logs.list = AsyncMock(return_value={"logs": [{"id": "1"}]})
    mcp, _ = build_mcp(register_audit_tools)

    result = await mcp.call_tool("termix_list_session_logs", {})
    assert result.structured_content["logs"] == [{"id": "1"}]


async def test_get_session_log_metadata_only(build_mcp, mock_client) -> None:
    mock_client.session_logs.retrieve = AsyncMock(return_value={"log": {"id": "1"}})
    mcp, _ = build_mcp(register_audit_tools)

    result = await mcp.call_tool("termix_get_session_log", {"session_log_id": "1"})
    assert "content" not in result.structured_content
    mock_client.session_logs.get_content.assert_not_called()


async def test_get_session_log_with_content_truncates(build_mcp, mock_client) -> None:
    mock_client.session_logs.retrieve = AsyncMock(return_value={"log": {"id": "1"}})
    long_text = "x" * 50
    stream = AsyncMock()
    stream.read = AsyncMock(return_value=long_text.encode())
    mock_client.session_logs.get_content = AsyncMock(return_value=stream)
    mcp, _ = build_mcp(register_audit_tools)

    result = await mcp.call_tool(
        "termix_get_session_log",
        {"session_log_id": "1", "include_content": True, "max_chars": 10},
    )
    assert result.structured_content["content"] == "x" * 10
    assert result.structured_content["content_truncated"] is True
    assert result.structured_content["content_total_chars"] == 50


async def test_get_session_log_with_content_no_truncation_needed(build_mcp, mock_client) -> None:
    mock_client.session_logs.retrieve = AsyncMock(return_value={"log": {"id": "1"}})
    stream = AsyncMock()
    stream.read = AsyncMock(return_value=b"short")
    mock_client.session_logs.get_content = AsyncMock(return_value=stream)
    mcp, _ = build_mcp(register_audit_tools)

    result = await mcp.call_tool(
        "termix_get_session_log",
        {"session_log_id": "1", "include_content": True, "max_chars": 100},
    )
    assert result.structured_content["content"] == "short"
    assert result.structured_content["content_truncated"] is False
    assert "content_total_chars" not in result.structured_content
