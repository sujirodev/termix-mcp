"""tunnels toolset (opt-in): SSH tunnels (connect/disconnect-by-name) and presets.

SDK surface: client.tunnel, client.tunnel_presets. Tunnels here are named, ephemeral
resources, not a persisted CRUD row: `tunnel.connect()` both creates and starts one,
`tunnel.disconnect(tunnelName=...)` stops it, `tunnel.get_status()`/`get_status_by_name()`
are the list/get. `TunnelConnectParams` has ~45 fields (source/endpoint SSH auth,
SOCKS5, retry policy...); only a minimal subset for a basic local-forward tunnel is
exposed here (D7: curated schema, not full passthrough). Persisted tunnel presets
(`tunnel_presets.py`) are a separate, simpler CRUD resource.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field
from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings
from termix_mcp.policy import guarded
from termix_mcp.shaping import simplify_dict


def register_tunnels_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="tunnels", read_only=True, idempotent=True)
    async def termix_list_tunnels() -> dict[str, Any]:
        """Status de todos os tuneis SSH ativos."""
        result = await client.tunnel.get_status()
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="tunnels", read_only=True, idempotent=True)
    async def termix_get_tunnel(
        tunnel_name: Annotated[str, Field(description="Nome do tunel")],
    ) -> dict[str, Any]:
        """Status de um tunel SSH especifico pelo nome."""
        result = await client.tunnel.get_status_by_name(tunnel_name)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="tunnels", read_only=False, flags={"data-access"})
    async def termix_create_tunnel(
        name: Annotated[str, Field(description="Nome unico do tunel")],
        source_host_id: Annotated[
            int, Field(description="ID do host de origem (que abre o tunel)")
        ],
        mode: Annotated[
            Literal["local", "remote", "dynamic"], Field(description="Tipo de encaminhamento")
        ],
        source_port: Annotated[int, Field(description="Porta local do tunel", ge=1, le=65535)],
        target_host: Annotated[
            str | None, Field(description="Host de destino (modo local/remote)")
        ] = None,
        local_address: Annotated[
            str | None, Field(description="Endereco local a expor (modo local)")
        ] = None,
        remote_address: Annotated[
            str | None, Field(description="Endereco remoto a expor (modo remote)")
        ] = None,
        auto_start: Annotated[bool, Field(description="Reconecta automaticamente")] = False,
    ) -> dict[str, Any]:
        """Cria e conecta um tunel SSH. Expoe apenas um subconjunto curado dos campos do
        Termix (nao cobre todas as opcoes de SOCKS5/retry da API)."""
        params: dict[str, Any] = {
            "name": name,
            "sourceHostId": source_host_id,
            "mode": mode,
            "sourcePort": source_port,
            "autoStart": auto_start,
        }
        if target_host is not None:
            params["targetHost"] = target_host
        if local_address is not None:
            params["localAddress"] = local_address
        if remote_address is not None:
            params["remoteAddress"] = remote_address
        result = await client.tunnel.connect(**params)
        return simplify_dict(result)

    @guarded(
        mcp,
        settings,
        toolset="tunnels",
        read_only=False,
        idempotent=True,
        flags={"data-access"},
    )
    async def termix_delete_tunnel(
        tunnel_name: Annotated[str, Field(description="Nome do tunel a desconectar")],
    ) -> dict[str, Any]:
        """Desconecta um tunel SSH ativo."""
        result = await client.tunnel.disconnect(tunnelName=tunnel_name)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="tunnels", read_only=True, idempotent=True)
    async def termix_list_tunnel_presets() -> dict[str, Any]:
        """Lista os presets de tunel salvos (configuracoes reutilizaveis)."""
        presets = await client.tunnel_presets.list()
        return simplify_dict(presets, max_items=settings.mcp_max_items)
