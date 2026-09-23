from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_automations import register_automations_tools


async def test_list_automations_happy_path(build_mcp, mock_client) -> None:
    mock_client.automations.list = AsyncMock(return_value=[{"id": "1", "name": "backup"}])
    mcp, _ = build_mcp(register_automations_tools, TERMIX_MCP_TOOLSETS="automations")

    result = await mcp.call_tool("termix_list_automations", {})
    assert result.structured_content["total"] == 1


async def test_get_automation_happy_path(build_mcp, mock_client) -> None:
    mock_client.automations.retrieve = AsyncMock(return_value={"id": "1", "name": "backup"})
    mcp, _ = build_mcp(register_automations_tools, TERMIX_MCP_TOOLSETS="automations")

    result = await mcp.call_tool("termix_get_automation", {"automation_id": "1"})
    assert result.structured_content["name"] == "backup"


async def test_run_automation_defaults_no_dry_run(build_mcp, mock_client) -> None:
    mock_client.automations.run = AsyncMock(return_value={"runId": 1, "status": "success"})
    mcp, _ = build_mcp(register_automations_tools, TERMIX_MCP_TOOLSETS="automations")

    result = await mcp.call_tool("termix_run_automation", {"automation_id": "1"})
    assert result.structured_content["status"] == "success"
    mock_client.automations.run.assert_awaited_once_with("1", dryRun=False)


async def test_run_automation_dry_run(build_mcp, mock_client) -> None:
    mock_client.automations.run = AsyncMock(return_value={"runId": 1, "status": "success"})
    mcp, _ = build_mcp(register_automations_tools, TERMIX_MCP_TOOLSETS="automations")

    await mcp.call_tool("termix_run_automation", {"automation_id": "1", "dry_run": True})
    mock_client.automations.run.assert_awaited_once_with("1", dryRun=True)


async def test_list_fleets_happy_path(build_mcp, mock_client) -> None:
    mock_client.fleets.list = AsyncMock(return_value=[{"id": "1", "name": "web-fleet"}])
    mcp, _ = build_mcp(register_automations_tools, TERMIX_MCP_TOOLSETS="automations")

    result = await mcp.call_tool("termix_list_fleets", {})
    assert result.structured_content["total"] == 1


async def test_write_tools_absent_in_read_only_mode(build_mcp) -> None:
    mcp, _ = build_mcp(
        register_automations_tools, TERMIX_MCP_TOOLSETS="automations", TERMIX_MCP_READ_ONLY="true"
    )

    assert await mcp.get_tool("termix_list_automations") is not None
    assert await mcp.get_tool("termix_run_automation") is None
