from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from termix_mcp.client import build_client
from termix_mcp.config import Settings
from termix_mcp.resources.server_info import register_server_info_resource
from termix_mcp.tools.registry import register_all_tools


def configure_logging(settings: Settings) -> None:
    # stdio transport speaks MCP over stdout; logs must never land there.
    stream = sys.stdout if settings.mcp_transport == "http" else sys.stderr
    logging.basicConfig(
        level=settings.mcp_log_level,
        stream=stream,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_server(settings: Settings) -> FastMCP:
    client = build_client(settings)

    @asynccontextmanager
    async def lifespan(_app: FastMCP) -> AsyncIterator[None]:
        try:
            yield None
        finally:
            await client.close()

    mcp = FastMCP(
        name="termix-mcp",
        instructions=(
            "Gerencia hosts, snippets, dashboard, metricas, sistema e auditoria de uma "
            "instancia Termix. Read-only e toolsets sao configurados por variaveis de "
            "ambiente TERMIX_MCP_*; veja o resource termix://server/info para o estado "
            "atual desta instancia."
        ),
        lifespan=lifespan,
    )

    register_server_info_resource(mcp, client, settings)
    register_all_tools(mcp, client, settings)

    return mcp
