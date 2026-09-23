"""audit toolset: audit log, session log listing and (truncated) content.

SDK surface: client.audit, client.session_logs. `audit.list()` paginates via `page`/
`limit`, both typed as `str` in the SDK's TypedDict (not `int`) - the tool still takes
`int` params and stringifies them for the call. `session_logs.get_content()` returns a
raw byte stream with no truncation parameter; truncation to `max_chars` happens here,
client-side, after reading the whole stream.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_audit_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="audit", read_only=True, idempotent=True)
    async def termix_list_audit_events(
        page: Annotated[int, Field(description="Numero da pagina, comecando em 1", ge=1)] = 1,
        limit: Annotated[int, Field(description="Itens por pagina", ge=1, le=200)] = 50,
    ) -> dict[str, Any]:
        """Lista eventos de auditoria (quem fez o que, quando)."""
        result = await client.audit.list(page=str(page), limit=str(limit))
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="audit", read_only=True, idempotent=True)
    async def termix_list_session_logs() -> dict[str, Any]:
        """Lista os logs de sessao (terminal) gravados."""
        logs = await client.session_logs.list()
        return simplify_dict(logs, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="audit", read_only=True, idempotent=True)
    async def termix_get_session_log(
        session_log_id: Annotated[str, Field(description="ID do log de sessao")],
        include_content: Annotated[
            bool, Field(description="Tambem buscar e incluir o conteudo gravado da sessao")
        ] = False,
        max_chars: Annotated[
            int, Field(description="Trunca o conteudo neste numero de caracteres", ge=1, le=100_000)
        ] = 4000,
    ) -> dict[str, Any]:
        """Metadados de um log de sessao; opcionalmente inclui o conteudo gravado,
        truncado em `max_chars` (a API do Termix nao trunca no servidor)."""
        log = await client.session_logs.retrieve(session_log_id)
        result = simplify_dict(log)

        if include_content:
            content_response = await client.session_logs.get_content(session_log_id)
            raw = (await content_response.read()).decode("utf-8", errors="replace")
            truncated = len(raw) > max_chars
            result["content"] = raw[:max_chars]
            result["content_truncated"] = truncated
            if truncated:
                result["content_total_chars"] = len(raw)

        return result
