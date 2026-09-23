from __future__ import annotations

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from termix_sdk import NotFoundError

from termix_mcp.policy import guarded
from termix_mcp.tools.toolsets import TOOL_TABLE


async def test_read_only_tool_is_registered(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings()

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_list_hosts() -> list[str]:
        return []

    assert await mcp.get_tool("termix_list_hosts") is not None
    assert TOOL_TABLE["termix_list_hosts"].read_only is True


async def test_write_tool_not_registered_in_read_only_mode(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_READ_ONLY="true")

    @guarded(mcp, settings, toolset="hosts", read_only=False, destructive=True)
    async def termix_delete_host() -> dict[str, object]:
        return {}

    assert await mcp.get_tool("termix_delete_host") is None
    # still tracked in the catalog even though it wasn't exposed
    assert "termix_delete_host" in TOOL_TABLE


async def test_write_tool_blocked_at_call_time_even_if_referenced_directly(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_READ_ONLY="true")

    @guarded(mcp, settings, toolset="hosts", read_only=False)
    async def termix_delete_host() -> dict[str, object]:
        return {"ok": True}

    with pytest.raises(ToolError, match="TERMIX_MCP_READ_ONLY"):
        await termix_delete_host()


async def test_tool_not_registered_when_toolset_disabled(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_TOOLSETS="snippets")

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_list_hosts() -> list[str]:
        return []

    assert await mcp.get_tool("termix_list_hosts") is None


async def test_disabled_tools_denylist_wins_over_toolset(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_DISABLED_TOOLS="termix_list_hosts")

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_list_hosts() -> list[str]:
        return []

    assert await mcp.get_tool("termix_list_hosts") is None


async def test_enabled_tools_allowlist_excludes_others(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_ENABLED_TOOLS="termix_get_host")

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_list_hosts() -> list[str]:
        return []

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_get_host() -> dict[str, object]:
        return {}

    assert await mcp.get_tool("termix_list_hosts") is None
    assert await mcp.get_tool("termix_get_host") is not None


async def test_termix_error_mapped_to_tool_error(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings()

    @guarded(mcp, settings, toolset="hosts", read_only=True)
    async def termix_get_host() -> dict[str, object]:
        raise NotFoundError("no such host")

    with pytest.raises(ToolError):
        await termix_get_host()
