from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastmcp import FastMCP
from termix_sdk import AuthenticationError

from termix_mcp.resources.server_info import register_server_info_resource


async def test_server_info_reports_reachable_when_healthy(make_settings) -> None:
    mcp = FastMCP()
    client = MagicMock()
    client.system.health = AsyncMock(return_value={"status": "ok"})
    client.system.version = AsyncMock(return_value={"version": "2.8.0"})
    settings = make_settings()

    register_server_info_resource(mcp, client, settings)

    result = await mcp.read_resource("termix://server/info")
    payload = result.contents[0].content
    assert isinstance(payload, str)
    assert '"reachable":true' in payload.replace(" ", "")
    assert '"toolsets_active"' in payload


async def test_server_info_reports_unreachable_on_termix_error(make_settings) -> None:
    mcp = FastMCP()
    client = MagicMock()
    client.system.health = AsyncMock(side_effect=AuthenticationError("bad key", http_status=401))
    settings = make_settings()

    register_server_info_resource(mcp, client, settings)

    result = await mcp.read_resource("termix://server/info")
    payload = result.contents[0].content
    assert isinstance(payload, str)
    assert '"reachable":false' in payload.replace(" ", "")
