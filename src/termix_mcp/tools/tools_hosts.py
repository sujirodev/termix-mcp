"""hosts toolset: SSH hosts, folders, autostart, network topology.

SDK surface: client.hosts (termix_sdk.resources.hosts) and client.network_topology.
`get_network_topology` lives in the network_topology resource, not hosts, despite being
grouped in the `hosts` toolset (see plano-implementacao.md section 6.1). There is no
dedicated "list host tags" endpoint; termix_list_host_tags derives tags client-side from
hosts.list(). HostsCreateParams/HostsUpdateParams have ~90 fields; only a curated subset
useful for an agent is exposed here (D7: hand-written schemas over full passthrough).
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

# Fields the GET returns that are not inputs to the PUT (identity, timestamps, sharing
# metadata); `has*` flags are filtered by prefix alongside these.
_HOST_RESPONSE_ONLY_FIELDS = frozenset(
    {
        "id",
        "userId",
        "createdAt",
        "updatedAt",
        "ownerId",
        "ownerUsername",
        "isShared",
        "permissionLevel",
        "sharedExpiresAt",
        "authOverrides",
    }
)


def _shaped(value: Any, *, max_items: int | None = None) -> dict[str, Any]:
    return cast(dict[str, Any], redact(simplify(value, max_items=max_items)))


def _build_host_params(
    *,
    name: str | None = None,
    connection_type: str | None = None,
    ip: str | None = None,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    key: str | None = None,
    key_password: str | None = None,
    auth_type: str | None = None,
    folder: str | None = None,
    tags: list[str] | None = None,
    credential_id: str | None = None,
    enable_terminal: bool | None = None,
    enable_file_manager: bool | None = None,
    enable_docker: bool | None = None,
    enable_tunnel: bool | None = None,
) -> dict[str, Any]:
    raw = {
        "name": name,
        "connectionType": connection_type,
        "ip": ip,
        "port": port,
        "username": username,
        "password": password,
        "key": key,
        "keyPassword": key_password,
        "authType": auth_type,
        "folder": folder,
        "tags": tags,
        "credentialId": credential_id,
        "enableTerminal": enable_terminal,
        "enableFileManager": enable_file_manager,
        "enableDocker": enable_docker,
        "enableTunnel": enable_tunnel,
    }
    return {key: value for key, value in raw.items() if value is not None}


def register_hosts_tools(mcp: FastMCP, client: AsyncTermixClient, settings: Settings) -> None:
    @guarded(mcp, settings, toolset="hosts", read_only=True, idempotent=True)
    async def termix_list_hosts(
        folder: Annotated[str | None, Field(description="Filtra por pasta exata")] = None,
        tag: Annotated[str | None, Field(description="Filtra por tag exata")] = None,
        text: Annotated[
            str | None, Field(description="Filtra por texto no nome ou IP (case-insensitive)")
        ] = None,
    ) -> dict[str, Any]:
        """Lista os hosts SSH cadastrados no Termix, com filtros opcionais aplicados no
        cliente (a API do Termix nao suporta filtro server-side)."""
        hosts = cast(list[dict[str, Any]], redact(simplify(await client.hosts.list())))
        if folder is not None:
            hosts = [h for h in hosts if h.get("folder") == folder]
        if tag is not None:
            hosts = [h for h in hosts if tag in (h.get("tags") or [])]
        if text is not None:
            needle = text.lower()

            def _matches(h: dict[str, Any]) -> bool:
                return (
                    needle in str(h.get("name", "")).lower()
                    or needle in str(h.get("ip", "")).lower()
                )

            hosts = [h for h in hosts if _matches(h)]
        return simplify_dict(hosts, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="hosts", read_only=True, idempotent=True)
    async def termix_get_host(
        host_id: Annotated[str, Field(description="ID do host")],
    ) -> dict[str, Any]:
        """Detalhes de um host SSH especifico."""
        host = await client.hosts.retrieve(host_id)
        return _shaped(host)

    @guarded(mcp, settings, toolset="hosts", read_only=False)
    async def termix_create_host(
        name: Annotated[str, Field(description="Nome de exibicao do host")],
        ip: Annotated[str, Field(description="IP ou hostname")],
        username: Annotated[str, Field(description="Usuario SSH")],
        port: Annotated[int, Field(description="Porta SSH", ge=1, le=65535)] = 22,
        connection_type: Annotated[
            str, Field(description="Tipo de conexao: ssh, rdp, vnc ou telnet")
        ] = "ssh",
        auth_type: Annotated[str | None, Field(description="password, key ou credential")] = None,
        password: Annotated[str | None, Field(description="Senha SSH (texto plano)")] = None,
        key: Annotated[str | None, Field(description="Chave privada SSH (texto plano)")] = None,
        key_password: Annotated[str | None, Field(description="Senha da chave privada")] = None,
        credential_id: Annotated[
            str | None,
            Field(description="ID de uma credencial ja cadastrada, em vez de segredo inline"),
        ] = None,
        folder: Annotated[str | None, Field(description="Pasta onde organizar o host")] = None,
        tags: Annotated[list[str] | None, Field(description="Tags do host")] = None,
        enable_terminal: Annotated[bool | None, Field(description="Habilita terminal")] = None,
        enable_file_manager: Annotated[
            bool | None, Field(description="Habilita gerenciador de arquivos")
        ] = None,
        enable_docker: Annotated[bool | None, Field(description="Habilita painel Docker")] = None,
        enable_tunnel: Annotated[bool | None, Field(description="Habilita tuneis")] = None,
    ) -> dict[str, Any]:
        """Cria um novo host SSH. Use `credential_id` em vez de senha/chave inline sempre
        que possivel, para nao passar segredos pela chamada da tool."""
        params = _build_host_params(
            name=name,
            connection_type=connection_type,
            ip=ip,
            port=port,
            username=username,
            password=password,
            key=key,
            key_password=key_password,
            auth_type=auth_type,
            folder=folder,
            tags=tags,
            credential_id=credential_id,
            enable_terminal=enable_terminal,
            enable_file_manager=enable_file_manager,
            enable_docker=enable_docker,
            enable_tunnel=enable_tunnel,
        )
        created = await client.hosts.create(**params)
        return _shaped(created)

    @guarded(mcp, settings, toolset="hosts", read_only=False, idempotent=True)
    async def termix_update_host(
        host_id: Annotated[str, Field(description="ID do host a atualizar")],
        name: Annotated[str | None, Field(description="Novo nome de exibicao")] = None,
        ip: Annotated[str | None, Field(description="Novo IP ou hostname")] = None,
        port: Annotated[int | None, Field(description="Nova porta SSH", ge=1, le=65535)] = None,
        username: Annotated[str | None, Field(description="Novo usuario SSH")] = None,
        auth_type: Annotated[str | None, Field(description="password, key ou credential")] = None,
        password: Annotated[str | None, Field(description="Nova senha SSH (texto plano)")] = None,
        key: Annotated[str | None, Field(description="Nova chave privada SSH")] = None,
        key_password: Annotated[
            str | None, Field(description="Nova senha da chave privada")
        ] = None,
        credential_id: Annotated[str | None, Field(description="Nova credencial associada")] = None,
        folder: Annotated[str | None, Field(description="Nova pasta")] = None,
        tags: Annotated[
            list[str] | None, Field(description="Novas tags (substitui as atuais)")
        ] = None,
        enable_terminal: Annotated[
            bool | None, Field(description="Habilita/desabilita terminal")
        ] = None,
        enable_file_manager: Annotated[
            bool | None, Field(description="Habilita/desabilita gerenciador de arquivos")
        ] = None,
        enable_docker: Annotated[
            bool | None, Field(description="Habilita/desabilita painel Docker")
        ] = None,
        enable_tunnel: Annotated[
            bool | None, Field(description="Habilita/desabilita tuneis")
        ] = None,
    ) -> dict[str, Any]:
        """Atualiza campos de um host SSH existente. Campos omitidos nao sao alterados:
        o PUT do Termix substitui o registro inteiro (tags/flags/credentialId omitidos
        viram vazio), entao a tool le o host atual e envia o merge. Senha/chave atuais
        sao preservadas pelo backend quando nao enviadas (host.ts, release-2.8.0)."""
        params = _build_host_params(
            name=name,
            ip=ip,
            port=port,
            username=username,
            password=password,
            key=key,
            key_password=key_password,
            auth_type=auth_type,
            folder=folder,
            tags=tags,
            credential_id=credential_id,
            enable_terminal=enable_terminal,
            enable_file_manager=enable_file_manager,
            enable_docker=enable_docker,
            enable_tunnel=enable_tunnel,
        )
        current = simplify_dict(await client.hosts.retrieve(host_id))
        merged = {
            key: value
            for key, value in current.items()
            if key not in _HOST_RESPONSE_ONLY_FIELDS and not key.startswith("has")
        }
        merged.update(params)
        updated = await client.hosts.update(host_id, **merged)
        return _shaped(updated)

    @guarded(mcp, settings, toolset="hosts", read_only=False, destructive=True, idempotent=True)
    async def termix_delete_host(
        host_id: Annotated[str, Field(description="ID do host a remover")],
    ) -> dict[str, Any]:
        """Remove um host SSH permanentemente. Nao ha confirmacao adicional; confirme com
        o usuario antes de chamar esta tool."""
        result = await client.hosts.delete(host_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="hosts", read_only=True, idempotent=True)
    async def termix_list_host_folders() -> dict[str, Any]:
        """Lista as pastas usadas para organizar hosts."""
        folders = simplify(await client.hosts.list_folders())
        return simplify_dict(folders, max_items=settings.mcp_max_items)

    @guarded(mcp, settings, toolset="hosts", read_only=True, idempotent=True)
    async def termix_list_host_tags() -> dict[str, Any]:
        """Lista as tags em uso, derivadas do campo `tags` de cada host (o Termix nao tem
        um endpoint dedicado para isso)."""
        hosts = simplify(await client.hosts.list())
        unique_tags = sorted({tag for h in hosts for tag in (h.get("tags") or [])})
        return {"tags": unique_tags, "total": len(unique_tags)}

    @guarded(mcp, settings, toolset="hosts", read_only=False, idempotent=True)
    async def termix_enable_host_autostart(
        ssh_config_id: Annotated[int, Field(description="ID da configuracao SSH")],
    ) -> dict[str, Any]:
        """Habilita autostart para uma configuracao SSH."""
        result = await client.hosts.enable_autostart(sshConfigId=ssh_config_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="hosts", read_only=False, idempotent=True)
    async def termix_disable_host_autostart(
        ssh_config_id: Annotated[int, Field(description="ID da configuracao SSH")],
    ) -> dict[str, Any]:
        """Desabilita autostart para uma configuracao SSH."""
        result = await client.hosts.disable_autostart(sshConfigId=ssh_config_id)
        return simplify_dict(result)

    @guarded(mcp, settings, toolset="hosts", read_only=True, idempotent=True)
    async def termix_get_network_topology() -> dict[str, Any]:
        """Topologia de rede salva para o usuario dono da API key. Retorna vazio se nunca
        foi salva."""
        topology = await client.network_topology.get()
        if topology is None:
            return {"topology": None}
        return _shaped(topology)
