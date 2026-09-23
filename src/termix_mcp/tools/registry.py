"""Discovers `tools_*.py` modules and registers their tools with the FastMCP instance.

A module that fails to import is logged and skipped rather than crashing the server -
one broken toolset shouldn't take the rest down.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

from fastmcp import FastMCP
from termix_sdk import AsyncTermixClient

from termix_mcp import tools as tools_package
from termix_mcp.config import Settings

logger = logging.getLogger("termix_mcp.registry")


def register_all_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    prefix = f"{tools_package.__name__}."
    for module_info in pkgutil.iter_modules(tools_package.__path__, prefix=prefix):
        module_name = module_info.name
        short_name = module_name.rsplit(".", 1)[-1]
        if not short_name.startswith("tools_"):
            continue

        try:
            module = importlib.import_module(module_name)
        except Exception:
            logger.exception("Falha ao importar modulo de tools '%s'; pulando.", module_name)
            continue

        domain = short_name.removeprefix("tools_")
        register_fn_name = f"register_{domain}_tools"
        register_fn = getattr(module, register_fn_name, None)
        if register_fn is None:
            logger.warning(
                "Modulo '%s' nao tem a funcao esperada '%s'; pulando.",
                module_name,
                register_fn_name,
            )
            continue

        try:
            register_fn(mcp, client, settings)
        except Exception:
            logger.exception("Falha ao registrar tools do modulo '%s'; pulando.", module_name)
