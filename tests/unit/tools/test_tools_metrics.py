from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError
from termix_sdk import NotFoundError

from termix_mcp.tools.tools_metrics import register_metrics_tools


async def test_get_host_metrics_happy_path(build_mcp, mock_client) -> None:
    mock_client.metrics.get_metrics = AsyncMock(return_value={"cpu": {"percent": 12}})
    mcp, _ = build_mcp(register_metrics_tools)

    result = await mcp.call_tool("termix_get_host_metrics", {"host_id": "1"})
    assert result.structured_content["cpu"]["percent"] == 12


async def test_get_host_metrics_not_found(build_mcp, mock_client) -> None:
    mock_client.metrics.get_metrics = AsyncMock(side_effect=NotFoundError("no host"))
    mcp, _ = build_mcp(register_metrics_tools)

    with pytest.raises(ToolError):
        await mcp.call_tool("termix_get_host_metrics", {"host_id": "x"})


async def test_get_metrics_history_happy_path(build_mcp, mock_client) -> None:
    mock_client.metrics.get_metrics_history = AsyncMock(
        return_value={"rows": [{"t": 1}, {"t": 2}], "fromTs": "a", "toTs": "b"}
    )
    mcp, _ = build_mcp(register_metrics_tools)

    result = await mcp.call_tool("termix_get_metrics_history", {"host_id": "1"})
    assert result.structured_content["fromTs"] == "a"


async def test_get_host_status_happy_path(build_mcp, mock_client) -> None:
    mock_client.metrics.get_status = AsyncMock(return_value={"status": "online"})
    mcp, _ = build_mcp(register_metrics_tools)

    result = await mcp.call_tool("termix_get_host_status", {"host_id": "1"})
    assert result.structured_content["status"] == "online"


async def test_list_host_statuses_without_filter(build_mcp, mock_client) -> None:
    mock_client.metrics.list_statuses = AsyncMock(return_value={"statuses": []})
    mcp, _ = build_mcp(register_metrics_tools)

    await mcp.call_tool("termix_list_host_statuses", {})
    mock_client.metrics.list_statuses.assert_awaited_once_with()


async def test_list_host_statuses_with_filter(build_mcp, mock_client) -> None:
    mock_client.metrics.list_statuses = AsyncMock(return_value={"statuses": []})
    mcp, _ = build_mcp(register_metrics_tools)

    await mcp.call_tool("termix_list_host_statuses", {"host_ids": ["1", "2"]})
    mock_client.metrics.list_statuses.assert_awaited_once_with(hostIds="1,2")


async def test_get_proxmox_stats_happy_path(build_mcp, mock_client) -> None:
    mock_client.proxmox_stats.retrieve = AsyncMock(return_value={"node": {"cpu": 0.1}})
    mcp, _ = build_mcp(register_metrics_tools)

    result = await mcp.call_tool("termix_get_proxmox_stats", {"host_id": "1"})
    assert result.structured_content["node"]["cpu"] == 0.1


async def test_list_active_alerts_happy_path(build_mcp, mock_client) -> None:
    mock_client.alerts.list = AsyncMock(
        return_value={"alerts": [{"id": "1"}], "cached": False, "total_count": 1}
    )
    mcp, _ = build_mcp(register_metrics_tools)

    result = await mcp.call_tool("termix_list_active_alerts", {})
    assert result.structured_content["total_count"] == 1


async def test_all_metrics_tools_are_read_only(build_mcp) -> None:
    from termix_mcp.tools.toolsets import TOOL_TABLE

    build_mcp(register_metrics_tools)
    assert len(TOOL_TABLE) == 6
    assert all(meta.read_only for meta in TOOL_TABLE.values())
