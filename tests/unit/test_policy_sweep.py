"""Sweeps the full tool catalog for the two hard security guarantees from
plano-implementacao.md section 10: the default toolset never carries admin/data-access/
dangerous tools, and read-only mode never exposes a write tool - across every toolset,
not just the ones exercised in tests/unit/tools/test_tools_*.py individually.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastmcp import FastMCP

from termix_mcp.tools.registry import register_all_tools
from termix_mcp.tools.toolsets import TOOL_TABLE


async def test_default_toolsets_never_expose_privileged_flags(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings()  # TERMIX_MCP_TOOLSETS unset -> "default"
    register_all_tools(mcp, MagicMock(), settings)

    registered_names = {t.name for t in await mcp.list_tools()}
    assert len(registered_names) > 0

    for meta in TOOL_TABLE.values():
        if meta.name not in registered_names:
            continue  # in the catalog (every toolset registers metadata) but not exposed
        assert meta.toolset in {"hosts", "snippets", "dashboard", "metrics", "system", "audit"}
        assert "admin" not in meta.flags
        assert "dangerous" not in meta.flags
        assert "data-access" not in meta.flags


async def test_read_only_blocks_every_write_tool_across_all_toolsets(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_TOOLSETS="all,admin", TERMIX_MCP_READ_ONLY="true")
    register_all_tools(mcp, MagicMock(), settings)

    registered_names = {t.name for t in await mcp.list_tools()}
    assert len(registered_names) > 0

    for meta in TOOL_TABLE.values():
        if meta.name in registered_names:
            assert meta.read_only, f"{meta.name} is a write tool but is registered under READ_ONLY"


async def test_tool_table_matches_registered_tools_exactly(make_settings) -> None:
    mcp = FastMCP()
    settings = make_settings(TERMIX_MCP_TOOLSETS="all,admin")
    register_all_tools(mcp, MagicMock(), settings)

    registered_names = {t.name for t in await mcp.list_tools()}
    assert registered_names == set(TOOL_TABLE.keys())
