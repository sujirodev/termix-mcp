"""snippets toolset: reusable command snippets and running them on a host.

SDK surface: client.snippets (termix_sdk.resources.snippets). `execute()` is the run
call; its params are `snippetId`/`hostId` (both int), not `id`/`host_id`.
"""

from __future__ import annotations

from typing import Annotated, Any, cast

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.redaction import redact
from termix_mcp.shaping import simplify, simplify_dict


def _shaped(value: Any, *, max_items: int | None = None) -> dict[str, Any]:
    return cast(dict[str, Any], redact(simplify(value, max_items=max_items)))


def register_snippets_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="snippets", read_only=True, idempotent=True)
    async def termix_list_snippets() -> dict[str, Any]:
        """Lista os snippets de comando cadastrados."""
        snippets = await client.snippets.list()
        return simplify_dict(snippets, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="snippets", read_only=True, idempotent=True)
    async def termix_get_snippet(
        snippet_id: Annotated[str, Field(description="ID do snippet")],
    ) -> dict[str, Any]:
        """Detalhes de um snippet especifico, incluindo o conteudo do comando."""
        snippet = await client.snippets.retrieve(snippet_id)
        return simplify_dict(snippet)

    @guarded(mcp, settings, toolset="snippets", read_only=False)
    async def termix_create_snippet(
        name: Annotated[str, Field(description="Nome do snippet")],
        content: Annotated[str, Field(description="Conteudo do comando/script")],
        description: Annotated[str | None, Field(description="Descricao opcional")] = None,
        folder: Annotated[str | None, Field(description="Pasta onde organizar")] = None,
        host_filter: Annotated[
            str | None, Field(description="Filtro opcional de quais hosts podem rodar isto")
        ] = None,
    ) -> dict[str, Any]:
        """Cria um novo snippet de comando."""
        params: dict[str, Any] = {"name": name, "content": content}
        if description is not None:
            params["description"] = description
        if folder is not None:
            params["folder"] = folder
        if host_filter is not None:
            params["hostFilter"] = host_filter
        created = await client.snippets.create(**params)
        return simplify_dict(created)

    @guarded(mcp, settings, toolset="snippets", read_only=False, idempotent=True)
    async def termix_update_snippet(
        snippet_id: Annotated[str, Field(description="ID do snippet a atualizar")],
        name: Annotated[str | None, Field(description="Novo nome")] = None,
        content: Annotated[str | None, Field(description="Novo conteudo do comando/script")] = None,
        description: Annotated[str | None, Field(description="Nova descricao")] = None,
        folder: Annotated[str | None, Field(description="Nova pasta")] = None,
        host_filter: Annotated[str | None, Field(description="Novo filtro de hosts")] = None,
    ) -> dict[str, Any]:
        """Atualiza campos de um snippet existente. Campos omitidos nao sao alterados."""
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if content is not None:
            params["content"] = content
        if description is not None:
            params["description"] = description
        if folder is not None:
            params["folder"] = folder
        if host_filter is not None:
            params["hostFilter"] = host_filter
        updated = await client.snippets.update(snippet_id, **params)
        return simplify_dict(updated)

    @guarded(mcp, settings, toolset="snippets", read_only=False, destructive=True, idempotent=True)
    async def termix_delete_snippet(
        snippet_id: Annotated[str, Field(description="ID do snippet a remover")],
    ) -> dict[str, Any]:
        """Remove um snippet permanentemente."""
        result = await client.snippets.delete(snippet_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="snippets", read_only=False)
    async def termix_run_snippet(
        snippet_id: Annotated[int, Field(description="ID do snippet a executar")],
        host_id: Annotated[int, Field(description="ID do host onde executar")],
        input_values: Annotated[
            dict[str, Any] | None,
            Field(description="Valores para variaveis de entrada do snippet, se houver"),
        ] = None,
    ) -> dict[str, Any]:
        """Executa um snippet em um host real via SSH. Isto tem efeito colateral no host
        de destino; confirme com o usuario antes de chamar, a menos que ele ja tenha
        pedido explicitamente para rodar este comando."""
        result = await client.snippets.execute(
            snippetId=snippet_id, hostId=host_id, inputValues=input_values or {}
        )
        return _shaped(result)
