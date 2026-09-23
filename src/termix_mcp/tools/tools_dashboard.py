"""dashboard toolset: uptime/activity/service links, workspaces, open tabs, homepage.

SDK surface: client.dashboard, client.homepage, client.workspaces, client.open_tabs.
There is no single "dashboard summary" or "homepage" endpoint in the SDK - both tools
here compose two calls each. `workspaces` has no read-only `retrieve`/`get`; only
`apply(id)` exists and it has the side effect of marking the workspace "just used", so
no `termix_get_workspace` tool is exposed (see plano-implementacao.md deviations).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify, simplify_dict


def register_dashboard_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="dashboard", read_only=True, idempotent=True)
    async def termix_get_dashboard_summary(
        activity_limit: Annotated[
            int, Field(description="Quantos eventos de atividade recente incluir", ge=1, le=200)
        ] = 20,
    ) -> dict[str, Any]:
        """Resumo do dashboard: uptime do Termix, atividade recente e links de servico
        configurados (nao ha um endpoint unico; combina tres chamadas)."""
        uptime = await client.dashboard.uptime()
        activity = await client.dashboard.list_recent_activity(limit=activity_limit)
        links = await client.dashboard.list_service_links()
        return {
            "uptime": simplify(uptime),
            "recent_activity": simplify(activity, max_items=activity_limit),
            "service_links": simplify(links, max_items=settings.mcp_max_items),
        }

    @guarded(mcp, settings, toolset="dashboard", read_only=True, idempotent=True)
    async def termix_list_workspaces() -> dict[str, Any]:
        """Lista os workspaces salvos do usuario dono da API key."""
        workspaces = await client.workspaces.list()
        return simplify_dict(workspaces, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="dashboard", read_only=True, idempotent=True)
    async def termix_list_open_tabs() -> dict[str, Any]:
        """Lista as abas abertas salvas do usuario dono da API key."""
        tabs = await client.open_tabs.list()
        return simplify_dict(tabs, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="dashboard", read_only=True, idempotent=True)
    async def termix_get_homepage() -> dict[str, Any]:
        """Itens e layout da homepage configurada (combina duas chamadas: list_items e
        get_layout)."""
        items = await client.homepage.list_items()
        layout = await client.homepage.get_layout()
        return {
            "homepage_items": simplify(items, max_items=settings.mcp_max_items),
            "layout": simplify(layout) if layout is not None else None,
        }
