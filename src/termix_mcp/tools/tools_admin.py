"""admin toolset (never on by default, never implied by `all` - must be named
explicitly in TERMIX_MCP_TOOLSETS): instance-wide, read-mostly configuration.

SDK surface: client.instance_settings, client.encryption, client.sso, client.termix_id.
Only the read-only subset plus branding update is exposed (D5/D per
plano-implementacao.md section 6.3) - nothing that touches auth/SSO/encryption
configuration itself.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_admin_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_branding() -> dict[str, Any]:
        """Configuracao de branding da instancia (nome, tagline, logo)."""
        result = await client.instance_settings.get_branding()
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="admin", read_only=False, idempotent=True, flags={"admin"})
    async def termix_update_branding(
        app_name: Annotated[str | None, Field(description="Nome da aplicacao")] = None,
        tagline: Annotated[str | None, Field(description="Tagline")] = None,
        logo: Annotated[str | None, Field(description="URL ou dado do logo")] = None,
    ) -> dict[str, Any]:
        """Atualiza o branding da instancia. Requer privilegio de admin."""
        params: dict[str, Any] = {}
        if app_name is not None:
            params["appName"] = app_name
        if tagline is not None:
            params["tagline"] = tagline
        if logo is not None:
            params["logo"] = logo
        result = await client.instance_settings.update_branding(**params)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_host_defaults() -> dict[str, Any]:
        """Configuracoes default aplicadas a hosts novos (ex.: proxy SOCKS5)."""
        result = await client.instance_settings.get_host_defaults()
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_audit_forwarding() -> dict[str, Any]:
        """Configuracao de encaminhamento de logs de auditoria (nunca expoe o token)."""
        result = await client.instance_settings.get_audit_forwarding()
        return simplify_dict(result, drop=("token",))

    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_encryption_status() -> dict[str, Any]:
        """Status de criptografia dos dados da instancia (somente leitura)."""
        result = await client.encryption.get_status()
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_list_sso_providers() -> dict[str, Any]:
        """Lista todos os provedores SSO configurados, incluindo desabilitados.
        Requer privilegio de admin."""
        providers = await client.sso.list_providers_admin()
        return simplify_dict(providers, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="admin", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_termix_id_status() -> dict[str, Any]:
        """Status do Termix ID (identidade federada) do usuario dono da API key."""
        result = await client.termix_id.get_me()
        return simplify_dict(result)
