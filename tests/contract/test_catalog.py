"""Contract tests over the tool catalog: every input schema is valid JSON Schema, the
serialized catalog is deterministic, and it matches the committed snapshot. A change to
any tool's name, parameters, description or annotations fails here until the snapshot is
regenerated on purpose:

    uv run pytest tests/contract --snapshot-update
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP
from jsonschema.validators import validator_for

from termix_mcp.config import Settings
from termix_mcp.tools import toolsets
from termix_mcp.tools.registry import register_all_tools

SNAPSHOT = Path(__file__).with_name("catalog_snapshot.json")


async def _catalog() -> list[dict[str, Any]]:
    toolsets.reset_table()
    settings = Settings(
        TERMIX_URL="https://example.invalid",
        TERMIX_API_KEY="tmx_placeholder",
        TERMIX_MCP_TOOLSETS="all,admin",
    )
    mcp = FastMCP()
    register_all_tools(mcp, MagicMock(), settings)
    tools = await mcp.list_tools()
    entries = []
    for tool in sorted(tools, key=lambda t: t.name):
        meta = toolsets.TOOL_TABLE[tool.name]
        entries.append(
            {
                "name": tool.name,
                "toolset": meta.toolset,
                "flags": sorted(meta.flags),
                "description": tool.description,
                "annotations": {
                    "read_only_hint": tool.annotations.read_only_hint if tool.annotations else None,
                    "destructive_hint": tool.annotations.destructive_hint
                    if tool.annotations
                    else None,
                    "idempotent_hint": tool.annotations.idempotent_hint
                    if tool.annotations
                    else None,
                    "open_world_hint": tool.annotations.open_world_hint
                    if tool.annotations
                    else None,
                },
                "input_schema": tool.parameters,
            }
        )
    return entries


async def test_every_input_schema_is_valid_json_schema() -> None:
    for entry in await _catalog():
        schema = entry["input_schema"]
        validator_for(schema).check_schema(schema)


async def test_every_tool_has_annotations_and_description() -> None:
    for entry in await _catalog():
        assert entry["description"], entry["name"]
        assert entry["annotations"]["read_only_hint"] is not None, entry["name"]
        assert entry["annotations"]["open_world_hint"] is True, entry["name"]


async def test_catalog_is_deterministic() -> None:
    first = json.dumps(await _catalog(), sort_keys=True)
    second = json.dumps(await _catalog(), sort_keys=True)
    assert first == second


async def test_catalog_matches_snapshot(request: pytest.FixtureRequest) -> None:
    current = json.dumps(await _catalog(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if request.config.getoption("--snapshot-update"):
        SNAPSHOT.write_text(current, encoding="utf-8")
        pytest.skip("snapshot updated")
    assert SNAPSHOT.exists(), "run: uv run pytest tests/contract --snapshot-update"
    assert current == SNAPSHOT.read_text(encoding="utf-8"), (
        "tool catalog changed; review the diff and run "
        "`uv run pytest tests/contract --snapshot-update`"
    )
