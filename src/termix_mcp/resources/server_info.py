from __future__ import annotations

from importlib.metadata import version as pkg_version
from typing import Any

from fastmcp import FastMCP
from termix_sdk import SPEC_VERSION, AsyncTermixClient, TermixError

from termix_mcp.config import Settings
from termix_mcp.shaping import simplify


def register_server_info_resource(
    mcp: FastMCP, client: AsyncTermixClient, settings: Settings
) -> None:
    @mcp.resource(
        "termix://server/info",
        name="server_info",
        title="Termix MCP server info",
        description=(
            "Diagnostico: versoes, toolsets ativos, modo read-only, conectividade com o Termix."
        ),
        mime_type="application/json",
    )
    async def server_info() -> dict[str, Any]:
        try:
            mcp_version = pkg_version("termix-mcp")
        except Exception:
            mcp_version = "0.0.0+dev"

        try:
            sdk_version = pkg_version("termix-sdk")
        except Exception:
            sdk_version = "unknown"

        connectivity: dict[str, Any] = {"reachable": None, "termix_version": None, "error": None}
        try:
            health = await client.system.health()
            version_info = await client.system.version()
            connectivity["reachable"] = simplify(health).get("status") == "ok"
            connectivity["termix_version"] = simplify(version_info)
        except TermixError as exc:
            connectivity["reachable"] = False
            connectivity["error"] = exc.user_message

        return {
            "termix_mcp_version": mcp_version,
            "termix_sdk_version": sdk_version,
            "termix_sdk_spec_version": SPEC_VERSION,
            "toolsets_active": sorted(settings.toolsets),
            "read_only": settings.mcp_read_only,
            "redact_secrets": settings.mcp_redact_secrets,
            "transport": settings.mcp_transport,
            "termix": connectivity,
        }
