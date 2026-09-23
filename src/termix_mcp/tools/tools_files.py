"""files toolset (opt-in): remote filesystem operations over a real SSH session.

SDK surface: client.file_manager, opened per call via `termix_sdk.async_ssh_session`
(D6: session per call, no persistent session in v1). Calls through the session handle
are keyword-only and never take `session_id`/`sessionId` - the helper injects it. There
is no "stat a single file" endpoint and `read_file` has no server-side byte-size limit
(termix_read_file truncates client-side via `max_chars`).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient, async_ssh_session

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_files_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="files", read_only=True, idempotent=True, flags={"data-access"})
    async def termix_list_files(
        host_id: Annotated[str, Field(description="ID do host")],
        path: Annotated[str, Field(description="Diretorio a listar")] = "/",
    ) -> dict[str, Any]:
        """Lista arquivos e diretorios em um caminho de um host, via sessao SSH aberta
        e fechada dentro desta chamada."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.list_files(path=path)
        return simplify_dict(result, max_items=settings.mcp_max_items)

    @guarded(
        mcp,
        settings,
        toolset="files",
        read_only=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_read_file(
        host_id: Annotated[str, Field(description="ID do host")],
        path: Annotated[str, Field(description="Caminho do arquivo")],
        max_chars: Annotated[
            int, Field(description="Trunca o conteudo neste numero de caracteres", ge=1, le=200_000)
        ] = 20_000,
    ) -> dict[str, Any]:
        """Le o conteudo de um arquivo remoto, truncado em `max_chars` (a API do Termix
        nao limita tamanho no servidor)."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.read_file(path=path)
        shaped = simplify_dict(result)
        content = shaped.get("content")
        if isinstance(content, str) and len(content) > max_chars:
            shaped["content"] = content[:max_chars]
            shaped["content_truncated"] = True
            shaped["content_total_chars"] = len(content)
        return shaped

    @guarded(mcp, settings, toolset="files", read_only=False, flags={"data-access"})
    async def termix_write_file(
        host_id: Annotated[str, Field(description="ID do host")],
        path: Annotated[str, Field(description="Caminho do arquivo")],
        content: Annotated[str, Field(description="Conteudo a escrever (sobrescreve)")],
    ) -> dict[str, Any]:
        """Escreve (sobrescreve) o conteudo de um arquivo remoto."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.write_file(path=path, content=content)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="files",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_create_folder(
        host_id: Annotated[str, Field(description="ID do host")],
        path: Annotated[str, Field(description="Diretorio pai")],
        folder_name: Annotated[str, Field(description="Nome da nova pasta")],
    ) -> dict[str, Any]:
        """Cria um diretorio remoto."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.create_folder(path=path, folderName=folder_name)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="files",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_move_file(
        host_id: Annotated[str, Field(description="ID do host")],
        old_path: Annotated[str, Field(description="Caminho atual")],
        new_path: Annotated[str, Field(description="Novo caminho")],
    ) -> dict[str, Any]:
        """Move (ou renomeia entre diretorios) um arquivo ou diretorio remoto."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.move_item(oldPath=old_path, newPath=new_path)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="files",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_rename_file(
        host_id: Annotated[str, Field(description="ID do host")],
        old_path: Annotated[str, Field(description="Caminho atual")],
        new_name: Annotated[str, Field(description="Novo nome (mesmo diretorio)")],
    ) -> dict[str, Any]:
        """Renomeia um arquivo ou diretorio remoto, mantendo o diretorio."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.rename_item(oldPath=old_path, newName=new_name)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="files",
        read_only=False,
        destructive=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_delete_file(
        host_id: Annotated[str, Field(description="ID do host")],
        path: Annotated[str, Field(description="Caminho a remover")],
        is_directory: Annotated[bool, Field(description="Se o caminho e um diretorio")] = False,
        permanent: Annotated[
            bool, Field(description="Remove permanentemente (pula a lixeira)")
        ] = False,
    ) -> dict[str, Any]:
        """Remove um arquivo ou diretorio remoto. Por padrao vai para a lixeira do
        Termix (`permanent=False`); confirme com o usuario antes de usar `permanent=True`."""
        async with async_ssh_session(client.file_manager, host_id=host_id) as fm:
            result = await fm.delete_item(path=path, isDirectory=is_directory, permanent=permanent)
        return simplify_dict(result)
