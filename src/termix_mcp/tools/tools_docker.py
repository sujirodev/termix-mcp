"""docker toolset (opt-in): containers on a host, over a real SSH session.

SDK surface: client.docker, opened per call via `async_ssh_session` (same session-per-
call model as `files`). There is no image-listing endpoint in this SDK version, so no
`termix_list_images` tool exists here. `DockerListContainersParams.all` is typed `str`
in the SDK; the Termix backend (`src/backend/hosts/docker/container-routes.ts`,
release-2.8.0) reads it as `req.query.all !== "false"`, so `"true"`/`"false"` is exact.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient, async_ssh_session

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_docker_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_list_containers(
        host_id: Annotated[str, Field(description="ID do host")],
        show_all: Annotated[
            bool, Field(description="Inclui containers parados, nao so os rodando")
        ] = True,
    ) -> dict[str, Any]:
        """Lista os containers Docker de um host."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.list_containers(all=str(show_all).lower())
        return simplify_dict(result, max_items=settings.mcp_max_items)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_get_container(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
    ) -> dict[str, Any]:
        """Detalhes de um container: imagem, estado, portas, montagens, redes."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.get_container(container_id=container_id)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_get_container_stats(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
    ) -> dict[str, Any]:
        """CPU, memoria, rede e disco em tempo real de um container."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.get_container_stats(container_id=container_id)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=True,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_get_container_logs(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
        tail: Annotated[
            int, Field(description="Numero de linhas do fim do log", ge=1, le=10_000)
        ] = 200,
        timestamps: Annotated[bool, Field(description="Inclui timestamp em cada linha")] = False,
    ) -> dict[str, Any]:
        """Logs recentes de um container (limitados por `tail`, ja suportado pela API)."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.get_container_logs(
                container_id=container_id, tail=tail, timestamps=timestamps
            )
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_start_container(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
    ) -> dict[str, Any]:
        """Inicia um container parado."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.start(container_id=container_id)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_stop_container(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
    ) -> dict[str, Any]:
        """Para um container rodando."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.stop(container_id=container_id)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="docker",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_restart_container(
        host_id: Annotated[str, Field(description="ID do host")],
        container_id: Annotated[str, Field(description="ID do container")],
    ) -> dict[str, Any]:
        """Reinicia um container."""
        async with async_ssh_session(client.docker, host_id=host_id) as docker:
            result = await docker.restart(container_id=container_id)
        return simplify_dict(result)
