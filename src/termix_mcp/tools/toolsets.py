"""Toolset taxonomy and the tool -> (toolset, flags, hints) registry.

`TOOL_TABLE` is populated at import time as a side effect of decorating each tool with
`policy.guarded`. Tests assert that every tool registered with FastMCP has an entry here
and vice-versa (see tests/unit/test_toolsets.py once tool modules exist).

`flags` conventions: `"admin"` for tools requiring Termix admin privilege, `"dangerous"`
reserved for the toolset in section 6.4 of the plan (none implemented in v1). `"data-access"`
is reserved for tools with *raw* access to secrets or an SSH session primitive (revealing a
credential, reading/writing a remote file, a Docker container, a tunnel) - never a tool in
the default toolset (`test_default_toolsets_never_expose_privileged_flags` enforces this).
`termix_run_snippet` executes a pre-registered, admin-curated snippet on a host and is a
default-toolset write tool, but it does *not* carry `data-access`: it's not raw access, and
plano-implementacao.md section 6.2 places it in the default toolset deliberately.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_TOOLSETS: frozenset[str] = frozenset(
    {"hosts", "snippets", "dashboard", "metrics", "system", "audit"}
)

OPT_IN_TOOLSETS: frozenset[str] = frozenset(
    {"credentials", "files", "docker", "tunnels", "alerts", "automations", "users"}
)

EXPLICIT_TOOLSETS: frozenset[str] = frozenset({"admin", "dangerous"})

ALL_KNOWN_TOOLSETS: frozenset[str] = DEFAULT_TOOLSETS | OPT_IN_TOOLSETS | EXPLICIT_TOOLSETS


def resolve_toolsets(requested: frozenset[str] | set[str]) -> frozenset[str]:
    """Expand the `default` / `all` shorthands; validate the rest against known toolsets.

    `all` expands to default + opt-in only. `admin` and `dangerous` are never implied by
    a shorthand and must be named explicitly (see toolsets.py docstring / D5).
    """
    resolved: set[str] = set()
    unknown: set[str] = set()

    for name in requested:
        if name == "default":
            resolved |= DEFAULT_TOOLSETS
        elif name == "all":
            resolved |= DEFAULT_TOOLSETS | OPT_IN_TOOLSETS
        elif name in ALL_KNOWN_TOOLSETS:
            resolved.add(name)
        else:
            unknown.add(name)

    if unknown:
        known = ", ".join(sorted(ALL_KNOWN_TOOLSETS | {"default", "all"}))
        raise ValueError(
            f"Toolset(s) desconhecido(s): {sorted(unknown)}. Toolsets validos: {known}."
        )

    return frozenset(resolved)


@dataclass(frozen=True, slots=True)
class ToolMeta:
    """What a tool is, for policy decisions and the generated docs table."""

    name: str
    toolset: str
    read_only: bool
    destructive: bool = False
    idempotent: bool = False
    flags: frozenset[str] = field(default_factory=frozenset)


TOOL_TABLE: dict[str, ToolMeta] = {}


def register_meta(meta: ToolMeta) -> None:
    if meta.name in TOOL_TABLE:
        raise ValueError(f"Tool '{meta.name}' ja esta registrada em toolsets.TOOL_TABLE")
    if meta.toolset not in ALL_KNOWN_TOOLSETS:
        raise ValueError(f"Toolset desconhecido para a tool '{meta.name}': {meta.toolset}")
    TOOL_TABLE[meta.name] = meta


def reset_table() -> None:
    """Test-only: clear TOOL_TABLE between test modules that re-import tool modules."""
    TOOL_TABLE.clear()
