from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_dashboard import register_dashboard_tools


async def test_get_dashboard_summary_composes_three_calls(build_mcp, mock_client) -> None:
    mock_client.dashboard.uptime = AsyncMock(return_value={"uptimeSeconds": 100})
    mock_client.dashboard.list_recent_activity = AsyncMock(return_value=[{"type": "login"}])
    mock_client.dashboard.list_service_links = AsyncMock(return_value=[{"label": "Grafana"}])
    mcp, _ = build_mcp(register_dashboard_tools)

    result = await mcp.call_tool("termix_get_dashboard_summary", {})

    assert result.structured_content["uptime"]["uptimeSeconds"] == 100
    assert result.structured_content["recent_activity"]["items"] == [{"type": "login"}]
    assert result.structured_content["service_links"]["items"] == [{"label": "Grafana"}]
    mock_client.dashboard.list_recent_activity.assert_awaited_once_with(limit=20)


async def test_get_dashboard_summary_respects_activity_limit(build_mcp, mock_client) -> None:
    mock_client.dashboard.uptime = AsyncMock(return_value={})
    mock_client.dashboard.list_recent_activity = AsyncMock(return_value=[])
    mock_client.dashboard.list_service_links = AsyncMock(return_value=[])
    mcp, _ = build_mcp(register_dashboard_tools)

    await mcp.call_tool("termix_get_dashboard_summary", {"activity_limit": 5})
    mock_client.dashboard.list_recent_activity.assert_awaited_once_with(limit=5)


async def test_list_workspaces_happy_path(build_mcp, mock_client) -> None:
    mock_client.workspaces.list = AsyncMock(return_value=[{"id": "1", "name": "default"}])
    mcp, _ = build_mcp(register_dashboard_tools)

    result = await mcp.call_tool("termix_list_workspaces", {})
    assert result.structured_content["total"] == 1


async def test_list_open_tabs_happy_path(build_mcp, mock_client) -> None:
    mock_client.open_tabs.list = AsyncMock(return_value=[{"id": "1", "tabType": "terminal"}])
    mcp, _ = build_mcp(register_dashboard_tools)

    result = await mcp.call_tool("termix_list_open_tabs", {})
    assert result.structured_content["items"][0]["tabType"] == "terminal"


async def test_get_homepage_composes_two_calls(build_mcp, mock_client) -> None:
    mock_client.homepage.list_items = AsyncMock(return_value=[{"id": "1", "title": "Grafana"}])
    mock_client.homepage.get_layout = AsyncMock(return_value={"entries": []})
    mcp, _ = build_mcp(register_dashboard_tools)

    result = await mcp.call_tool("termix_get_homepage", {})
    assert result.structured_content["homepage_items"]["items"][0]["title"] == "Grafana"
    assert result.structured_content["layout"] == {"entries": []}


async def test_get_homepage_handles_no_layout_saved(build_mcp, mock_client) -> None:
    mock_client.homepage.list_items = AsyncMock(return_value=[])
    mock_client.homepage.get_layout = AsyncMock(return_value=None)
    mcp, _ = build_mcp(register_dashboard_tools)

    result = await mcp.call_tool("termix_get_homepage", {})
    assert result.structured_content["layout"] is None


async def test_all_dashboard_tools_are_read_only(build_mcp) -> None:
    from termix_mcp.tools.toolsets import TOOL_TABLE

    build_mcp(register_dashboard_tools)
    assert len(TOOL_TABLE) == 4
    assert all(meta.read_only for meta in TOOL_TABLE.values())
