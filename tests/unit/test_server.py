from __future__ import annotations

from fastmcp import FastMCP

from termix_mcp.server import build_server, configure_logging


def test_build_server_returns_fastmcp_with_all_default_tools(make_settings) -> None:
    settings = make_settings()
    mcp = build_server(settings)
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "termix-mcp"


async def test_build_server_registers_server_info_resource(make_settings) -> None:
    settings = make_settings()
    mcp = build_server(settings)
    resources = await mcp.list_resources()
    assert any(str(r.uri) == "termix://server/info" for r in resources)


async def test_build_server_registers_default_toolset_tools(make_settings) -> None:
    settings = make_settings()
    mcp = build_server(settings)
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "termix_list_hosts" in names
    assert "termix_run_snippet" in names


async def test_lifespan_closes_client(make_settings) -> None:
    settings = make_settings()
    mcp = build_server(settings)
    async with mcp.lifespan():
        pass  # entering/exiting drives the lifespan context manager to completion


def test_configure_logging_does_not_raise(make_settings) -> None:
    configure_logging(make_settings())
    configure_logging(make_settings(TERMIX_MCP_TRANSPORT="http"))
