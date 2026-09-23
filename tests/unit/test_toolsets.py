from __future__ import annotations

import pytest

from termix_mcp.tools.toolsets import ToolMeta, register_meta, resolve_toolsets


def test_default_shorthand() -> None:
    assert resolve_toolsets({"default"}) == {
        "hosts",
        "snippets",
        "dashboard",
        "metrics",
        "system",
        "audit",
    }


def test_all_shorthand_excludes_explicit_toolsets() -> None:
    resolved = resolve_toolsets({"all"})
    assert "admin" not in resolved
    assert "dangerous" not in resolved
    assert "credentials" in resolved


def test_explicit_toolset_requires_exact_name() -> None:
    assert resolve_toolsets({"hosts", "admin"}) == {"hosts", "admin"}


def test_unknown_toolset_raises() -> None:
    with pytest.raises(ValueError, match="desconhecido"):
        resolve_toolsets({"not-a-real-toolset"})


def test_register_meta_rejects_duplicate_name() -> None:
    register_meta(ToolMeta(name="termix_ping", toolset="system", read_only=True))
    with pytest.raises(ValueError, match="ja esta registrada"):
        register_meta(ToolMeta(name="termix_ping", toolset="system", read_only=True))


def test_register_meta_rejects_unknown_toolset() -> None:
    with pytest.raises(ValueError, match="Toolset desconhecido"):
        register_meta(ToolMeta(name="termix_x", toolset="not-a-toolset", read_only=True))
