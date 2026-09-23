"""`guarded`: the one decorator every tool goes through.

It does four things: (1) registers the tool's metadata into `toolsets.TOOL_TABLE`, so the
catalog is always in sync with what's implemented; (2) decides whether the tool should be
exposed to the client at all, given the active toolsets/allowlist/denylist/read-only mode
(read-only layer 1: write tools don't even appear in the listing); (3) wraps the call so a
read-only violation is also caught at call time, in case a client cached an older tool list
(read-only layer 2); (4) maps `TermixError` to `ToolError` and logs usage without ever
logging tool arguments (which may carry secrets).
"""

from __future__ import annotations

import functools
import inspect
import logging
import time
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from termix_sdk import TermixError

from termix_mcp.config import Settings
from termix_mcp.errors import to_tool_error
from termix_mcp.tools.toolsets import ToolMeta, register_meta

logger = logging.getLogger("termix_mcp.tools")

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def _should_register(name: str, toolset: str, read_only: bool, settings: Settings) -> bool:
    if toolset not in settings.toolsets:
        return False
    if settings.mcp_read_only and not read_only:
        return False
    if settings.enabled_tools and name not in settings.enabled_tools:
        return False
    return name not in settings.disabled_tools


def guarded(
    mcp: FastMCP,
    settings: Settings,
    *,
    toolset: str,
    read_only: bool,
    destructive: bool = False,
    idempotent: bool = False,
    flags: Iterable[str] = (),
    title: str | None = None,
    description: str | None = None,
) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        name = fn.__name__
        flag_set = frozenset(flags)

        register_meta(
            ToolMeta(
                name=name,
                toolset=toolset,
                read_only=read_only,
                destructive=destructive,
                idempotent=idempotent,
                flags=flag_set,
            )
        )

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if settings.mcp_read_only and not read_only:
                raise ToolError(
                    f"'{name}' e uma operacao de escrita; bloqueada porque "
                    "TERMIX_MCP_READ_ONLY esta ativo."
                )
            start = time.monotonic()
            try:
                result = await fn(*args, **kwargs)
            except TermixError as exc:
                duration_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "tool=%s status=error error_class=%s duration_ms=%.1f",
                    name,
                    type(exc).__name__,
                    duration_ms,
                )
                raise to_tool_error(exc) from exc
            duration_ms = (time.monotonic() - start) * 1000
            logger.info("tool=%s status=ok duration_ms=%.1f", name, duration_ms)
            return result

        if _should_register(name, toolset, read_only, settings):
            mcp.tool(
                name=name,
                title=title,
                # cleandoc, not strip: Python 3.13+ dedents docstrings at compile time and
                # 3.11/3.12 don't, so without this the catalog differs by interpreter.
                description=description or inspect.cleandoc(fn.__doc__ or "") or None,
                tags={toolset} | flag_set,
                annotations=ToolAnnotations(
                    read_only_hint=read_only,
                    destructive_hint=destructive,
                    idempotent_hint=idempotent,
                    open_world_hint=True,
                ),
            )(wrapper)

        return wrapper  # type: ignore[return-value]

    return decorator
