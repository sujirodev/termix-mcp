from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ValidationError

from termix_mcp.tools.tools_alerts import register_alerts_tools


async def test_list_alert_rules_happy_path(build_mcp, mock_client) -> None:
    mock_client.alerts.list_rules = AsyncMock(return_value=[{"id": "1", "name": "cpu-high"}])
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    result = await mcp.call_tool("termix_list_alert_rules", {})
    assert result.structured_content["total"] == 1


async def test_create_alert_rule_with_defaults(build_mcp, mock_client) -> None:
    mock_client.alerts.create_rule = AsyncMock(return_value={"id": "1", "name": "cpu-high"})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    await mcp.call_tool(
        "termix_create_alert_rule",
        {
            "name": "cpu-high",
            "host_id": 5,
            "trigger_type": "cpu_threshold",
            "threshold_value": 90.0,
        },
    )
    mock_client.alerts.create_rule.assert_awaited_once_with(
        name="cpu-high",
        hostId=5,
        enabled=True,
        triggerType="cpu_threshold",
        thresholdValue=90.0,
        thresholdDurationSeconds=0,
        cooldownMinutes=15,
    )


async def test_create_alert_rule_with_channels(build_mcp, mock_client) -> None:
    mock_client.alerts.create_rule = AsyncMock(return_value={"id": "1"})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    await mcp.call_tool(
        "termix_create_alert_rule",
        {
            "name": "cpu-high",
            "host_id": 5,
            "trigger_type": "cpu_threshold",
            "threshold_value": 90.0,
            "channels": [1, 2],
        },
    )
    _, kwargs = mock_client.alerts.create_rule.await_args
    assert kwargs["channels"] == [1, 2]


async def test_create_alert_rule_without_host_or_threshold(build_mcp, mock_client) -> None:
    mock_client.alerts.create_rule = AsyncMock(return_value={"id": "2"})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    await mcp.call_tool(
        "termix_create_alert_rule", {"name": "logins", "trigger_type": "user_login"}
    )
    _, kwargs = mock_client.alerts.create_rule.await_args
    assert "hostId" not in kwargs
    assert "thresholdValue" not in kwargs
    assert kwargs["triggerType"] == "user_login"


async def test_create_alert_rule_rejects_unknown_trigger(build_mcp, mock_client) -> None:
    mock_client.alerts.create_rule = AsyncMock(return_value={"id": "3"})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    with pytest.raises(ValidationError):
        await mcp.call_tool(
            "termix_create_alert_rule", {"name": "x", "host_id": 1, "trigger_type": "cpu"}
        )
    mock_client.alerts.create_rule.assert_not_called()


async def test_delete_alert_rule_happy_path(build_mcp, mock_client) -> None:
    mock_client.alerts.delete_rule = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    result = await mcp.call_tool("termix_delete_alert_rule", {"rule_id": "1"})
    assert result.structured_content["success"] is True


async def test_acknowledge_alert_firing_happy_path(build_mcp, mock_client) -> None:
    mock_client.alerts.acknowledge_firing = AsyncMock(return_value={"success": True})
    mcp, _ = build_mcp(register_alerts_tools, TERMIX_MCP_TOOLSETS="alerts")

    result = await mcp.call_tool("termix_acknowledge_alert_firing", {"firing_id": "f1"})
    assert result.structured_content["success"] is True
    mock_client.alerts.acknowledge_firing.assert_awaited_once_with("f1")
