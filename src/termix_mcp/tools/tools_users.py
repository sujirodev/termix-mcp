"""users toolset (opt-in, admin-flagged tools): user directory, roles, access grants.

SDK surface: client.user_admin, client.rbac. `user_admin.list()` takes no
pagination params despite echoing `limit`/`offset` in its response. There is no
`get_user(id)` endpoint; `termix_get_user` derives it by listing and filtering
client-side (same pattern as `termix_list_host_tags` in the hosts toolset).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_users_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="users", read_only=True, idempotent=True, flags={"admin"})
    async def termix_list_users() -> dict[str, Any]:
        """Lista os usuarios do Termix. Requer privilegio de admin."""
        result = await client.user_admin.list()
        shaped = simplify_dict(result)
        users = shaped.get("users", [])
        return simplify_dict(users, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="users", read_only=True, idempotent=True, flags={"admin"})
    async def termix_get_user(
        user_id: Annotated[str, Field(description="ID do usuario")],
    ) -> dict[str, Any]:
        """Detalhes de um usuario especifico (nao ha endpoint dedicado; filtra a lista
        completa de usuarios). Requer privilegio de admin."""
        result = await client.user_admin.list()
        users = simplify_dict(result).get("users", [])
        for user in users:
            # Termix 2.8.0 returns `userId` here (confirmed E2E); `id` kept for older shapes.
            if str(user.get("userId", user.get("id"))) == str(user_id):
                return dict(user)
        raise ToolError(f"Usuario '{user_id}' nao encontrado.")

    @guarded(mcp, settings, toolset="users", read_only=True, idempotent=True, flags={"admin"})
    async def termix_list_roles() -> dict[str, Any]:
        """Lista os papeis (roles) RBAC disponiveis."""
        result = await client.rbac.list_roles()
        roles = simplify_dict(result).get("roles", [])
        return simplify_dict(roles, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="users", read_only=False, idempotent=True, flags={"admin"})
    async def termix_assign_role(
        user_id: Annotated[str, Field(description="ID do usuario")],
        role_id: Annotated[int, Field(description="ID do papel a atribuir")],
    ) -> dict[str, Any]:
        """Atribui um papel RBAC a um usuario. Requer privilegio de admin."""
        result = await client.rbac.assign_role(user_id, roleId=role_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="users", read_only=True, idempotent=True, flags={"admin"})
    async def termix_list_credential_access(
        credential_id: Annotated[str, Field(description="ID da credencial")],
    ) -> dict[str, Any]:
        """Lista com quem uma credencial esta compartilhada."""
        result = await client.rbac.list_credential_access(credential_id)
        access = simplify_dict(result).get("access", [])
        return simplify_dict(access, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="users", read_only=True, idempotent=True, flags={"admin"})
    async def termix_list_folder_access(
        folder: Annotated[str, Field(description="Nome da pasta")],
    ) -> dict[str, Any]:
        """Lista as regras de compartilhamento permanente de uma pasta de hosts."""
        result = await client.rbac.list_folder_access(folder=folder)
        rules = simplify_dict(result).get("rules", [])
        return simplify_dict(rules, max_items=settings.mcp_max_items)
