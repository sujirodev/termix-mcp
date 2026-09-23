"""Regenerates the tools table in README.md from `toolsets.TOOL_TABLE`.

Registers every tool (all toolsets, including `admin`) against a throwaway FastMCP
instance with a mock client - no network call happens, since registration only builds
the tool closures, it never invokes them.

Usage:
    uv run python scripts/generate_tool_docs.py          # rewrites README.md
    uv run python scripts/generate_tool_docs.py --check  # exit 1 if README.md is stale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastmcp import FastMCP

from termix_mcp.config import Settings
from termix_mcp.tools.registry import register_all_tools
from termix_mcp.tools.toolsets import TOOL_TABLE

START_MARKER = "<!-- TOOLS_TABLE_START -->"
END_MARKER = "<!-- TOOLS_TABLE_END -->"


def _build_table() -> str:
    settings = Settings(
        TERMIX_URL="https://example.invalid",
        TERMIX_API_KEY="tmx_placeholder",
        TERMIX_MCP_TOOLSETS="all,admin",
    )
    mcp = FastMCP()
    register_all_tools(mcp, MagicMock(), settings)

    lines = [
        "| Tool | Toolset | Read-only | Destructive | Flags |",
        "|---|---|:---:|:---:|---|",
    ]
    for meta in sorted(TOOL_TABLE.values(), key=lambda m: (m.toolset, m.name)):
        flags = ", ".join(sorted(meta.flags)) or "-"
        lines.append(
            f"| `{meta.name}` | {meta.toolset} | {'yes' if meta.read_only else 'no'} | "
            f"{'yes' if meta.destructive else 'no'} | {flags} |"
        )
    lines.append("")
    lines.append(f"Total: {len(TOOL_TABLE)} tools.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="nao escreve; falha se estiver desatualizado"
    )
    args = parser.parse_args()

    readme_path = Path(__file__).resolve().parent.parent / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    if START_MARKER not in content or END_MARKER not in content:
        print(f"README.md precisa dos marcadores {START_MARKER} / {END_MARKER}", file=sys.stderr)
        return 1

    before, rest = content.split(START_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    new_content = f"{before}{START_MARKER}\n{_build_table()}\n{END_MARKER}{after}"

    if args.check:
        if new_content != content:
            print(
                "README.md desatualizado; rode: uv run python scripts/generate_tool_docs.py",
                file=sys.stderr,
            )
            return 1
        return 0

    readme_path.write_text(new_content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
