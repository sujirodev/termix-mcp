from __future__ import annotations

from collections.abc import Iterator

import pytest

from termix_mcp.config import Settings
from termix_mcp.tools import toolsets


@pytest.fixture(autouse=True)
def _clean_tool_table() -> Iterator[None]:
    """Every test that decorates a tool with `policy.guarded` mutates the module-level
    TOOL_TABLE; reset it so tests don't leak registrations into each other."""
    toolsets.reset_table()
    yield
    toolsets.reset_table()


@pytest.fixture
def make_settings():
    def _make(**overrides: object) -> Settings:
        env = {
            "TERMIX_URL": "https://termix.example.com",
            "TERMIX_API_KEY": "tmx_testkey",
            **overrides,
        }
        return Settings(**env)  # type: ignore[arg-type]

    return _make
