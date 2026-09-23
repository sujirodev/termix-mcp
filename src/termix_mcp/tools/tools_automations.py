"""automations toolset (opt-in): list/inspect/run automations, list fleets.

SDK surface: client.automations, client.fleets. `get_automation` maps to
`automations.retrieve(id)` (no method is literally named `get`). Only list/get/run are
exposed, per plano-implementacao.md section 6.3 - mass-action fleet methods
(create/update/delete/execute-across-fleet) are out of scope for this toolset.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_automations_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="automations", read_only=True, idempotent=True)
    async def termix_list_automations() -> dict[str, Any]:
        """Lista as automacoes do usuario dono da API key."""
        automations = await client.automations.list()
        return simplify_dict(automations, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="automations", read_only=True, idempotent=True)
    async def termix_get_automation(
        automation_id: Annotated[str, Field(description="ID da automacao")],
    ) -> dict[str, Any]:
        """Detalhes de uma automacao especifica."""
        automation = await client.automations.retrieve(automation_id)
        return simplify_dict(automation)

    @guarded(mcp, settings, toolset="automations", read_only=False, flags={"data-access"})
    async def termix_run_automation(
        automation_id: Annotated[str, Field(description="ID da automacao a rodar")],
        dry_run: Annotated[bool, Field(description="Simula sem executar de verdade")] = False,
    ) -> dict[str, Any]:
        """Executa uma automacao agora. Isto tem efeito colateral real nos hosts
        alcancados pela automacao, a menos que `dry_run=True`; confirme com o usuario
        antes de rodar sem dry_run."""
        result = await client.automations.run(automation_id, dryRun=dry_run)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="automations", read_only=True, idempotent=True)
    async def termix_list_fleets() -> dict[str, Any]:
        """Lista as frotas (grupos de hosts) do usuario dono da API key."""
        fleets = await client.fleets.list()
        return simplify_dict(fleets, max_items=settings.mcp_max_items)
