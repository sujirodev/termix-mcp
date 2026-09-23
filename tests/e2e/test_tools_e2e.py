"""Every tool that doesn't need a reachable SSH host, end to end through FastMCP against a
real Termix. `files`/`docker` tools open a real SSH session and are marked `requires_ssh`
(only `live.yml` runs them, with an SSH container beside Termix).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import NotFoundError, ToolError
from termix_sdk import TermixClient

pytestmark = pytest.mark.e2e


async def _call(mcp: FastMCP, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    result = await mcp.call_tool(name, args or {})
    assert result.structured_content is not None
    return result.structured_content


async def test_server_info_resource_reports_reachable(mcp: FastMCP) -> None:
    result = await mcp.read_resource("termix://server/info")
    payload = result.contents[0].content
    assert isinstance(payload, str)
    assert '"reachable": true' in payload or '"reachable":true' in payload


async def test_all_toolsets_registered(mcp: FastMCP) -> None:
    names = {t.name for t in await mcp.list_tools()}
    assert "termix_list_hosts" in names
    assert "termix_get_branding" in names  # admin, enabled explicitly in conftest


# -- system ---------------------------------------------------------------------------


async def test_get_system_info(mcp: FastMCP) -> None:
    info = await _call(mcp, "termix_get_system_info")
    assert info["status"] == "ok"
    assert info["version"]


async def test_list_api_keys_never_returns_token(mcp: FastMCP, run_prefix: str) -> None:
    keys = await _call(mcp, "termix_list_api_keys")
    names = [k["name"] for k in keys["items"]]
    assert run_prefix in names
    assert all("token" not in k for k in keys["items"])


async def test_get_preferences(mcp: FastMCP) -> None:
    prefs = await _call(mcp, "termix_get_preferences")
    assert "theme" in prefs


# -- hosts ----------------------------------------------------------------------------


async def test_hosts_crud_through_tools(mcp: FastMCP, run_prefix: str) -> None:
    name = f"{run_prefix}-host"
    created = await _call(
        mcp,
        "termix_create_host",
        {
            "name": name,
            "ip": "10.0.0.1",
            "username": "root",
            "auth_type": "password",
            "password": "hunter2",
            "folder": run_prefix,
            "tags": [run_prefix],
        },
    )
    host_id = str(created["id"])
    assert created.get("password") in (None, "***")

    got = await _call(mcp, "termix_get_host", {"host_id": host_id})
    assert got["name"] == name

    listed = await _call(mcp, "termix_list_hosts", {"folder": run_prefix})
    assert [h["name"] for h in listed["items"]] == [name]

    by_tag = await _call(mcp, "termix_list_hosts", {"tag": run_prefix})
    assert by_tag["total"] == 1

    tags = await _call(mcp, "termix_list_host_tags")
    assert run_prefix in tags["tags"]

    # Termix 2.8.0 lists only folders with saved metadata, not names implied by hosts.
    folders = await _call(mcp, "termix_list_host_folders")
    assert "items" in folders

    updated = await _call(mcp, "termix_update_host", {"host_id": host_id, "name": f"{name}-r"})
    assert updated["name"] == f"{name}-r"

    await _call(mcp, "termix_delete_host", {"host_id": host_id})
    with pytest.raises(ToolError, match="nao encontrado"):
        await _call(mcp, "termix_get_host", {"host_id": host_id})


async def test_get_network_topology_when_unset(mcp: FastMCP) -> None:
    result = await _call(mcp, "termix_get_network_topology")
    assert "topology" in result or result  # either {"topology": None} or a saved topology


# -- snippets -------------------------------------------------------------------------


async def test_snippets_crud_through_tools(mcp: FastMCP, run_prefix: str) -> None:
    name = f"{run_prefix}-snippet"
    created = await _call(
        mcp, "termix_create_snippet", {"name": name, "content": "echo e2e", "folder": run_prefix}
    )
    snippet_id = str(created["id"])

    got = await _call(mcp, "termix_get_snippet", {"snippet_id": snippet_id})
    assert got["content"] == "echo e2e"

    listed = await _call(mcp, "termix_list_snippets")
    assert name in [s["name"] for s in listed["items"]]

    updated = await _call(
        mcp, "termix_update_snippet", {"snippet_id": snippet_id, "content": "echo e2e-2"}
    )
    assert updated.get("content", "echo e2e-2") == "echo e2e-2"
    got = await _call(mcp, "termix_get_snippet", {"snippet_id": snippet_id})
    assert got["content"] == "echo e2e-2"
    assert got["name"] == name

    await _call(mcp, "termix_delete_snippet", {"snippet_id": snippet_id})
    with pytest.raises(ToolError):
        await _call(mcp, "termix_get_snippet", {"snippet_id": snippet_id})


# -- dashboard ------------------------------------------------------------------------


async def test_dashboard_tools(mcp: FastMCP) -> None:
    summary = await _call(mcp, "termix_get_dashboard_summary", {"activity_limit": 5})
    assert summary["uptime"]["uptimeSeconds"] >= 0
    assert "items" in summary["recent_activity"]

    workspaces = await _call(mcp, "termix_list_workspaces")
    assert "items" in workspaces

    tabs = await _call(mcp, "termix_list_open_tabs")
    assert "items" in tabs

    homepage = await _call(mcp, "termix_get_homepage")
    assert "homepage_items" in homepage


# -- metrics --------------------------------------------------------------------------


async def test_metrics_status_tools_on_unreachable_host(mcp: FastMCP, run_prefix: str) -> None:
    created = await _call(
        mcp,
        "termix_create_host",
        {
            "name": f"{run_prefix}-metrics",
            "ip": "10.255.255.1",
            "username": "root",
            "auth_type": "password",
            "password": "x",
        },
    )
    host_id = str(created["id"])
    try:
        statuses = await _call(mcp, "termix_list_host_statuses", {"host_ids": [host_id]})
        assert statuses is not None
        alerts = await _call(mcp, "termix_list_active_alerts")
        assert "alerts" in alerts or "items" in alerts
    finally:
        await _call(mcp, "termix_delete_host", {"host_id": host_id})


# -- audit ----------------------------------------------------------------------------


async def test_audit_tools(mcp: FastMCP) -> None:
    events = await _call(mcp, "termix_list_audit_events", {"page": 1, "limit": 10})
    assert "logs" in events
    logs = await _call(mcp, "termix_list_session_logs")
    assert "logs" in logs or "items" in logs


# -- credentials (opt-in) -------------------------------------------------------------


async def test_credentials_crud_and_redaction(mcp: FastMCP, run_prefix: str) -> None:
    name = f"{run_prefix}-credential"
    created = await _call(
        mcp,
        "termix_create_credential",
        {"name": name, "auth_type": "password", "username": "root", "password": "hunter2"},
    )
    credential_id = str(created["id"])

    got = await _call(mcp, "termix_get_credential", {"credential_id": credential_id})
    assert got["name"] == name
    assert got.get("password") in (None, "***")

    revealed = await _call(mcp, "termix_reveal_credential", {"credential_id": credential_id})
    assert revealed.get("password") in (None, "***")  # REDACT_SECRETS defaults to true

    listed = await _call(mcp, "termix_list_credentials")
    assert name in [c["name"] for c in listed["items"]]

    await _call(
        mcp, "termix_update_credential", {"credential_id": credential_id, "name": f"{name}-r"}
    )
    await _call(mcp, "termix_delete_credential", {"credential_id": credential_id})
    with pytest.raises(ToolError):
        await _call(mcp, "termix_get_credential", {"credential_id": credential_id})


# -- tunnels / alerts / automations / users / admin (opt-in, read-mostly) ---------------


async def test_tunnel_read_tools(mcp: FastMCP) -> None:
    assert await _call(mcp, "termix_list_tunnels") is not None
    presets = await _call(mcp, "termix_list_tunnel_presets")
    assert "items" in presets


async def test_alert_rules_crud(mcp: FastMCP, run_prefix: str, sdk: TermixClient) -> None:
    host = sdk.hosts.create(
        name=f"{run_prefix}-alert-host",
        ip="10.0.0.2",
        port=22,
        username="root",
        authType="password",
    )
    host_id = int(host.to_dict()["id"])
    try:
        created = await _call(
            mcp,
            "termix_create_alert_rule",
            {
                "name": f"{run_prefix}-rule",
                "host_id": host_id,
                "trigger_type": "cpu_threshold",
                "threshold_value": 90.0,
            },
        )
        rule_id = str(created["id"])
        rules = await _call(mcp, "termix_list_alert_rules")
        assert rule_id in [str(r["id"]) for r in rules["items"]]
        await _call(mcp, "termix_delete_alert_rule", {"rule_id": rule_id})
    finally:
        sdk.hosts.delete(str(host_id))


async def test_automations_and_fleets_lists(mcp: FastMCP) -> None:
    assert "items" in await _call(mcp, "termix_list_automations")
    assert "items" in await _call(mcp, "termix_list_fleets")


async def test_users_and_roles(mcp: FastMCP) -> None:
    users = await _call(mcp, "termix_list_users")
    assert any(u["username"] == "ci" for u in users["items"])
    user_id = next(str(u["userId"]) for u in users["items"] if u["username"] == "ci")
    got = await _call(mcp, "termix_get_user", {"user_id": user_id})
    assert got["username"] == "ci"
    assert "items" in await _call(mcp, "termix_list_roles")


async def test_admin_read_tools(mcp: FastMCP) -> None:
    assert "appName" in await _call(mcp, "termix_get_branding")
    assert await _call(mcp, "termix_get_host_defaults") is not None
    forwarding = await _call(mcp, "termix_get_audit_forwarding")
    assert "token" not in forwarding
    assert "version" in await _call(mcp, "termix_get_encryption_status")
    assert "items" in await _call(mcp, "termix_list_sso_providers")
    assert "identity" in await _call(mcp, "termix_get_termix_id_status")


# -- policy against the real thing -----------------------------------------------------


async def test_read_only_server_hides_and_blocks_writes(mcp_read_only: FastMCP) -> None:
    names = {t.name for t in await mcp_read_only.list_tools()}
    assert "termix_list_hosts" in names
    assert "termix_create_host" not in names
    with pytest.raises(NotFoundError):  # FastMCP: the tool isn't exposed at all
        await mcp_read_only.call_tool(
            "termix_create_host", {"name": "x", "ip": "x", "username": "x"}
        )


async def test_invalid_api_key_maps_to_actionable_error(base_url: str) -> None:
    from termix_mcp.server import build_server
    from tests.e2e.conftest import make_settings

    server = build_server(make_settings(base_url, "tmx_invalid"))
    async with server.lifespan():
        with pytest.raises(ToolError, match="API key"):
            await server.call_tool("termix_list_hosts", {})


# -- requires a reachable SSH host ------------------------------------------------------


@pytest.mark.requires_ssh
async def test_files_over_ssh(mcp: FastMCP, sdk: TermixClient, run_prefix: str) -> None:
    """Needs TERMIX_E2E_SSH_HOST/_PORT/_USER/_PASSWORD pointing at a real sshd (live.yml
    starts linuxserver/openssh-server beside Termix)."""
    import os

    ssh_host = os.environ.get("TERMIX_E2E_SSH_HOST")
    if not ssh_host:
        pytest.skip("TERMIX_E2E_SSH_HOST not set")
    host = sdk.hosts.create(
        name=f"{run_prefix}-ssh",
        ip=ssh_host,
        port=int(os.environ.get("TERMIX_E2E_SSH_PORT", "2222")),
        username=os.environ.get("TERMIX_E2E_SSH_USER", "ci"),
        authType="password",
        password=os.environ.get("TERMIX_E2E_SSH_PASSWORD", ""),
    )
    host_id = str(host.to_dict()["id"])
    try:
        listing = await _call(mcp, "termix_list_files", {"host_id": host_id, "path": "/"})
        assert "files" in listing
    finally:
        sdk.hosts.delete(host_id)
