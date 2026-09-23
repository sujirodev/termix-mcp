"""system toolset: health/version, API key metadata, user preferences.

SDK surface used: client.system, client.api_keys, client.preferences (see
termix_sdk.resources.system/api_keys/preferences). There is no single "system info"
endpoint in the SDK; termix_get_system_info composes health() + version().
"""

from __future__ import annotations

from typing import Any, cast

from fastmcp import FastMCP
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.redaction import redact
from termix_mcp.shaping import simplify, simplify_dict


def register_system_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="system", read_only=True, idempotent=True)
    async def termix_get_system_info() -> dict[str, Any]:
        """Status de saude e versao do Termix conectado (nao ha um endpoint unico; combina
        health() e version() do SDK)."""
        health = await client.system.health()
        version_info = await client.system.version()
        return {
            "status": simplify_dict(health).get("status"),
            "version": simplify(version_info),
        }

    @guarded(mcp, settings, toolset="system", read_only=True, idempotent=True)
    async def termix_list_api_keys() -> dict[str, Any]:
        """Lista metadados das API keys cadastradas no Termix (nunca o valor do token).
        Requer privilegio de admin no Termix; falha com erro de permissao caso contrario."""
        result = await client.api_keys.list()
        api_keys = simplify_dict(result).get("apiKeys", [])
        return simplify_dict(api_keys, drop=("token",), max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="system", read_only=True, idempotent=True)
    async def termix_get_preferences() -> dict[str, Any]:
        """Preferencias do usuario dono da API key (tema, idioma, storage mode etc.)."""
        prefs = await client.preferences.get_user_preferences()
        return cast(dict[str, Any], redact(simplify(prefs)))
