"""alerts toolset (opt-in): alert rules and acknowledging firings.

SDK surface: client.alerts. `termix_list_active_alerts` (the currently-firing summary)
already lives in the default `metrics` toolset; this toolset manages rule configuration
and individual firing acknowledgement, which is a distinct concept in the SDK (alerts =
active-state summary, firings = individual rule-trigger events).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict

# VALID_TRIGGER_TYPES in Termix's src/backend/database/routes/alert-rules-routes.ts
# (release-2.8.0); anything else answers 400 "Invalid triggerType".
TriggerType = Literal[
    "host_offline",
    "host_online",
    "cpu_threshold",
    "memory_threshold",
    "disk_threshold",
    "health_check_failure",
    "health_check_recovery",
    "user_login",
]


def register_alerts_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="alerts", read_only=True, idempotent=True)
    async def termix_list_alert_rules() -> dict[str, Any]:
        """Lista as regras de alerta configuradas."""
        rules = await client.alerts.list_rules()
        return simplify_dict(rules, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="alerts", read_only=False)
    async def termix_create_alert_rule(
        name: Annotated[str, Field(description="Nome da regra")],
        trigger_type: Annotated[
            TriggerType,
            Field(description="Gatilho; os *_threshold usam threshold_value em porcentagem"),
        ],
        host_id: Annotated[
            int | None, Field(description="ID do host monitorado; omitido para user_login")
        ] = None,
        threshold_value: Annotated[
            float | None,
            Field(description="Limite em % (0-100) para gatilhos *_threshold", ge=0, le=100),
        ] = None,
        threshold_duration_seconds: Annotated[
            int, Field(description="Por quanto tempo o limite precisa se manter", ge=0)
        ] = 0,
        cooldown_minutes: Annotated[
            int, Field(description="Minutos de espera antes de disparar de novo", ge=0)
        ] = 15,
        enabled: Annotated[bool, Field(description="Se a regra comeca ativa")] = True,
        channels: Annotated[
            list[int] | None, Field(description="IDs dos canais de notificacao a usar")
        ] = None,
    ) -> dict[str, Any]:
        """Cria uma regra de alerta. Valores de gatilho e limites validados contra o
        backend do Termix 2.8.0 (alert-rules-routes.ts)."""
        params: dict[str, Any] = {
            "name": name,
            "enabled": enabled,
            "triggerType": trigger_type,
            "thresholdDurationSeconds": threshold_duration_seconds,
            "cooldownMinutes": cooldown_minutes,
        }
        if host_id is not None:
            params["hostId"] = host_id
        if threshold_value is not None:
            params["thresholdValue"] = threshold_value
        if channels is not None:
            params["channels"] = channels
        created = await client.alerts.create_rule(**params)
        return simplify_dict(created)

    @guarded(mcp, settings, toolset="alerts", read_only=False, destructive=True, idempotent=True)
    async def termix_delete_alert_rule(
        rule_id: Annotated[str, Field(description="ID da regra a remover")],
    ) -> dict[str, Any]:
        """Remove uma regra de alerta."""
        result = await client.alerts.delete_rule(rule_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="alerts", read_only=False, idempotent=True)
    async def termix_acknowledge_alert_firing(
        firing_id: Annotated[str, Field(description="ID do disparo de alerta")],
    ) -> dict[str, Any]:
        """Reconhece (acknowledge) um disparo de alerta especifico."""
        result = await client.alerts.acknowledge_firing(firing_id)
        return simplify_dict(result)
