from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastmcp import FastMCP

from termix_mcp import tools as tools_package
from termix_mcp.tools.registry import register_all_tools


async def test_register_all_tools_discovers_every_domain_module(make_settings) -> None:
    mcp = FastMCP()
    client = MagicMock()
    settings = make_settings()

    register_all_tools(mcp, client, settings)

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "termix_list_hosts" in names
    assert "termix_list_snippets" in names
    assert "termix_get_dashboard_summary" in names
    assert "termix_get_host_metrics" in names
    assert "termix_get_system_info" in names
    assert "termix_list_audit_events" in names


async def test_register_all_tools_respects_toolset_filter(make_settings) -> None:
    mcp = FastMCP()
    client = MagicMock()
    settings = make_settings(TERMIX_MCP_TOOLSETS="hosts")

    register_all_tools(mcp, client, settings)

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "termix_list_hosts" in names
    assert "termix_list_snippets" not in names


def test_register_all_tools_skips_module_that_fails_to_import(make_settings, monkeypatch) -> None:
    fake_module = SimpleNamespace(name=f"{tools_package.__name__}.tools_broken")
    monkeypatch.setattr(
        "termix_mcp.tools.registry.pkgutil.iter_modules", lambda *a, **kw: [fake_module]
    )

    mcp = FastMCP()
    register_all_tools(mcp, MagicMock(), make_settings())  # must not raise


def test_register_all_tools_skips_module_without_register_function(
    make_settings, monkeypatch
) -> None:
    fake_module = SimpleNamespace(name=f"{tools_package.__name__}.tools_incomplete")
    monkeypatch.setattr(
        "termix_mcp.tools.registry.pkgutil.iter_modules", lambda *a, **kw: [fake_module]
    )
    monkeypatch.setattr(
        "termix_mcp.tools.registry.importlib.import_module", lambda name: SimpleNamespace()
    )

    mcp = FastMCP()
    register_all_tools(mcp, MagicMock(), make_settings())  # must not raise


def test_register_all_tools_skips_module_whose_register_function_raises(
    make_settings, monkeypatch
) -> None:
    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom")

    fake_module = SimpleNamespace(name=f"{tools_package.__name__}.tools_exploding")
    monkeypatch.setattr(
        "termix_mcp.tools.registry.pkgutil.iter_modules", lambda *a, **kw: [fake_module]
    )
    monkeypatch.setattr(
        "termix_mcp.tools.registry.importlib.import_module",
        lambda name: SimpleNamespace(register_exploding_tools=_boom),
    )

    mcp = FastMCP()
    register_all_tools(mcp, MagicMock(), make_settings())  # must not raise
