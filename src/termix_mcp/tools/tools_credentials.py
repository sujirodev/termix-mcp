"""credentials toolset (opt-in): stored SSH credentials.

SDK surface: client.credentials. `retrieve(id)` returns an opaque object that can
include the raw secret (password/key/keyPassword), same fields as
CredentialsCreateParams - there is no separate "reveal" endpoint, so
`termix_get_credential` always redacts and `termix_reveal_credential` is the same call
with redaction conditional on `TERMIX_MCP_REDACT_SECRETS` (architecture section 4.5).
There is no "list vault items" endpoint; `vault.py` only manages Vault *profiles*
(connection config for an external secret store), a different concept, out of scope here.
"""

from __future__ import annotations

from typing import Annotated, Any, cast

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.redaction import redact
from termix_mcp.shaping import simplify_dict


def _redacted(value: Any, *, max_items: int | None = None) -> dict[str, Any]:
    return cast(dict[str, Any], redact(simplify_dict(value, max_items=max_items)))


def register_credentials_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="credentials", read_only=True, idempotent=True)
    async def termix_list_credentials() -> dict[str, Any]:
        """Lista credenciais cadastradas (metadados; segredos sempre mascarados)."""
        credentials = await client.credentials.list()
        return _redacted(credentials, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="credentials", read_only=True, idempotent=True)
    async def termix_get_credential(
        credential_id: Annotated[str, Field(description="ID da credencial")],
    ) -> dict[str, Any]:
        """Detalhes de uma credencial, com segredos sempre mascarados. Use
        `termix_reveal_credential` para obter o valor real."""
        credential = await client.credentials.retrieve(credential_id)
        return _redacted(credential)

    @guarded(mcp, settings, toolset="credentials", read_only=True, flags={"data-access"})
    async def termix_reveal_credential(
        credential_id: Annotated[str, Field(description="ID da credencial")],
    ) -> dict[str, Any]:
        """Detalhes de uma credencial incluindo o segredo em texto plano, apenas se
        `TERMIX_MCP_REDACT_SECRETS=false`. Com a configuracao padrao, este resultado sai
        mascarado igual a `termix_get_credential`."""
        credential = await client.credentials.retrieve(credential_id)
        shaped = simplify_dict(credential)
        if settings.mcp_redact_secrets:
            return _redacted(shaped)
        return shaped

    @guarded(mcp, settings, toolset="credentials", read_only=False)
    async def termix_create_credential(
        name: Annotated[str, Field(description="Nome da credencial")],
        auth_type: Annotated[str, Field(description="password ou key")],
        username: Annotated[str | None, Field(description="Usuario")] = None,
        password: Annotated[str | None, Field(description="Senha (se auth_type=password)")] = None,
        key: Annotated[str | None, Field(description="Chave privada (se auth_type=key)")] = None,
        key_password: Annotated[str | None, Field(description="Senha da chave privada")] = None,
        description: Annotated[str | None, Field(description="Descricao opcional")] = None,
        folder: Annotated[str | None, Field(description="Pasta onde organizar")] = None,
        tags: Annotated[list[str] | None, Field(description="Tags")] = None,
    ) -> dict[str, Any]:
        """Cria uma nova credencial reutilizavel para hosts."""
        params: dict[str, Any] = {"name": name, "authType": auth_type}
        for key_name, value in (
            ("username", username),
            ("password", password),
            ("key", key),
            ("keyPassword", key_password),
            ("description", description),
            ("folder", folder),
            ("tags", tags),
        ):
            if value is not None:
                params[key_name] = value
        created = await client.credentials.create(**params)
        return _redacted(created)

    @guarded(mcp, settings, toolset="credentials", read_only=False, idempotent=True)
    async def termix_update_credential(
        credential_id: Annotated[str, Field(description="ID da credencial")],
        name: Annotated[str | None, Field(description="Novo nome")] = None,
        username: Annotated[str | None, Field(description="Novo usuario")] = None,
        password: Annotated[str | None, Field(description="Nova senha")] = None,
        key: Annotated[str | None, Field(description="Nova chave privada")] = None,
        key_password: Annotated[str | None, Field(description="Nova senha da chave")] = None,
        description: Annotated[str | None, Field(description="Nova descricao")] = None,
        folder: Annotated[str | None, Field(description="Nova pasta")] = None,
        tags: Annotated[list[str] | None, Field(description="Novas tags")] = None,
    ) -> dict[str, Any]:
        """Atualiza campos de uma credencial existente."""
        params: dict[str, Any] = {}
        for key_name, value in (
            ("name", name),
            ("username", username),
            ("password", password),
            ("key", key),
            ("keyPassword", key_password),
            ("description", description),
            ("folder", folder),
            ("tags", tags),
        ):
            if value is not None:
                params[key_name] = value
        updated = await client.credentials.update(credential_id, **params)
        return _redacted(updated)

    @guarded(
        mcp,
        settings,
        toolset="credentials",
        read_only=False,
        destructive=True,
        idempotent=True,
    )
    async def termix_delete_credential(
        credential_id: Annotated[str, Field(description="ID da credencial")],
    ) -> dict[str, Any]:
        """Remove uma credencial permanentemente."""
        result = await client.credentials.delete(credential_id)
        return simplify_dict(result)
