"""metrics toolset: live/historical host metrics, status, Proxmox stats, active alerts.

SDK surface: client.metrics, client.proxmox_stats, client.alerts. `metrics.py` has ~46
methods; only the read-only, monitoring-relevant ones are exposed here. Two notable SDK
limitations carried over into the tool docstrings below: `get_metrics_history` has no
time-window parameters (the server picks the range), and there's no "list monitored
hosts" endpoint (`list_statuses` is the closest thing - it's a status check, not a
monitoring-enrollment list). `list_active_alerts` lives in `alerts.py`, not `metrics.py`,
despite being grouped in the `metrics` toolset (plano-implementacao.md section 6.1).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_metrics_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_get_host_metrics(
        host_id: Annotated[str, Field(description="ID do host")],
    ) -> dict[str, Any]:
        """Metricas atuais (CPU, memoria, disco, rede, uptime, processos) de um host."""
        metrics = await client.metrics.get_metrics(host_id)
        return simplify_dict(metrics)

    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_get_metrics_history(
        host_id: Annotated[str, Field(description="ID do host")],
    ) -> dict[str, Any]:
        """Historico de metricas de um host. O Termix decide a janela de tempo
        retornada (nao ha parametro de intervalo nesta versao do SDK); veja
        `termix_get_preferences`/retencao configurada para saber quanto historico existe."""
        history = await client.metrics.get_metrics_history(host_id)
        return simplify_dict(history, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_get_host_status(
        host_id: Annotated[str, Field(description="ID do host")],
    ) -> dict[str, Any]:
        """Status de conectividade (online/offline/reachable) de um host especifico."""
        status = await client.metrics.get_status(host_id)
        return simplify_dict(status)

    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_list_host_statuses(
        host_ids: Annotated[
            list[str] | None,
            Field(description="IDs dos hosts a consultar; omitido consulta todos"),
        ] = None,
    ) -> dict[str, Any]:
        """Status de conectividade de varios hosts de uma vez."""
        if host_ids:
            statuses = await client.metrics.list_statuses(hostIds=",".join(host_ids))
        else:
            statuses = await client.metrics.list_statuses()
        return simplify_dict(statuses)

    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_get_proxmox_stats(
        host_id: Annotated[str, Field(description="ID do host Proxmox")],
    ) -> dict[str, Any]:
        """Estatisticas (nos, storage, convidados) em cache de um host Proxmox."""
        stats = await client.proxmox_stats.retrieve(host_id)
        return simplify_dict(stats)

    @guarded(mcp, settings, toolset="metrics", read_only=True, idempotent=True)
    async def termix_list_active_alerts() -> dict[str, Any]:
        """Lista os alertas ativos no momento."""
        alerts = await client.alerts.list()
        return simplify_dict(alerts, max_items=settings.mcp_max_items)
