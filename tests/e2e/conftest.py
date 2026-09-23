"""Gate and bootstrap for the E2E suite: the MCP server against a real Termix.

Skipped unless `TERMIX_E2E=1`. With `TERMIX_E2E_BASE_URL` set, the suite uses that
instance; without it, it starts `docker/e2e/compose.yml` itself and tears it down at the
end (needs Docker). Bootstrap mirrors termix-sdk's tests/live/conftest.py: register a
user (the first account on an empty instance is admin), log in with JWT, mint an API key,
and run every tool through a real `build_server()` on that key.
"""

from __future__ import annotations

import contextlib
import os
import secrets
import subprocess
import time
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastmcp import FastMCP
from termix_sdk import NotFoundError, PendingTOTP, TermixClient, TermixError

from termix_mcp.config import Settings
from termix_mcp.server import build_server

if os.environ.get("TERMIX_E2E") != "1":
    pytest.skip("e2e: set TERMIX_E2E=1 to run this suite", allow_module_level=True)

pytestmark = pytest.mark.e2e

COMPOSE_FILE = Path(__file__).resolve().parents[2] / "docker" / "e2e" / "compose.yml"
BASE_URL = os.environ.get("TERMIX_E2E_BASE_URL", "")
USERNAME = os.environ.get("TERMIX_E2E_USER", "ci")
PASSWORD = os.environ.get("TERMIX_E2E_PASSWORD", "") or f"E2e-{secrets.token_hex(8)}-Aa1"
HEALTH_TIMEOUT_SECONDS = 120
HEALTH_INTERVAL_SECONDS = 2.0


@pytest.fixture(scope="session")
def base_url() -> Iterator[str]:
    if BASE_URL:
        yield BASE_URL
        return

    port = os.environ.get("TERMIX_E2E_PORT", "8080")
    compose = ["docker", "compose", "-f", str(COMPOSE_FILE)]
    subprocess.run([*compose, "up", "-d", "--wait"], check=True)
    try:
        yield f"http://localhost:{port}"
    finally:
        subprocess.run([*compose, "down", "-v"], check=False)


@pytest.fixture(scope="session")
def run_prefix() -> str:
    """Prefix for everything this run creates, so cleanup only touches its own rows."""
    return f"e2e-{secrets.token_hex(4)}"


@pytest.fixture(scope="session")
def _termix_is_up(base_url: str) -> None:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SECONDS
    last_error: Exception | None = None
    # Every client is closed explicitly: pytest runs with warnings-as-errors, and an
    # unclosed httpx transport surfaces as a ResourceWarning on the next test.
    with TermixClient(base_url=base_url, api_key="tmx_health_probe") as probe:
        while time.monotonic() < deadline:
            try:
                probe.system.health()
                return
            except TermixError as exc:
                last_error = exc
                time.sleep(HEALTH_INTERVAL_SECONDS)
    pytest.fail(f"{base_url}/health did not answer in {HEALTH_TIMEOUT_SECONDS}s: {last_error!r}")


@pytest.fixture(scope="session")
def jwt_client(base_url: str, _termix_is_up: None) -> Iterator[TermixClient]:
    with TermixClient(base_url=base_url, api_key="tmx_bootstrap_probe") as anonymous:
        try:
            anonymous.users.register(username=USERNAME, password=PASSWORD)
        except TermixError as exc:
            if exc.http_status is None or exc.http_status >= 500:
                raise
    client = TermixClient.login(base_url=base_url, username=USERNAME, password=PASSWORD)
    if isinstance(client, PendingTOTP):
        pytest.fail("the e2e instance must not have TOTP enabled for the ci user")
    with client:
        yield client


@pytest.fixture(scope="session")
def api_key(jwt_client: TermixClient, run_prefix: str) -> Iterator[str]:
    me = jwt_client.users.get_me().to_dict()
    if not me.get("is_admin"):
        pytest.skip(f"{USERNAME} is not an admin on this instance; api_keys.* is admin-only")
    created = jwt_client.api_keys.create(name=run_prefix, userId=me["userId"])
    yield created.token
    with contextlib.suppress(NotFoundError):
        jwt_client.api_keys.delete(created.id)


@pytest.fixture(scope="session")
def sdk(base_url: str, api_key: str, run_prefix: str) -> Iterator[TermixClient]:
    """Raw SDK client on the same API key, for setup/assertions outside the MCP path."""
    with TermixClient(base_url=base_url, api_key=api_key) as client:
        yield client
        _cleanup(client, run_prefix)


def make_settings(base_url: str, api_key: str, **overrides: str) -> Settings:
    env: dict[str, Any] = {
        "TERMIX_URL": base_url,
        "TERMIX_API_KEY": api_key,
        "TERMIX_MCP_TOOLSETS": "all,admin",
        **overrides,
    }
    return Settings(**env)


@pytest.fixture
async def mcp(base_url: str, api_key: str) -> AsyncIterator[FastMCP]:
    """Function-scoped: AsyncTermixClient binds its transport to the running loop, and
    pytest-asyncio gives every test its own loop."""
    server = build_server(make_settings(base_url, api_key))
    async with server.lifespan():
        yield server


@pytest.fixture
async def mcp_read_only(base_url: str, api_key: str) -> AsyncIterator[FastMCP]:
    server = build_server(make_settings(base_url, api_key, TERMIX_MCP_READ_ONLY="true"))
    async with server.lifespan():
        yield server


def _cleanup(client: TermixClient, run_prefix: str) -> None:
    """Delete whatever this run created and did not delete itself."""
    _delete_matching(client.hosts.list(), client.hosts.delete, run_prefix)
    _delete_matching(client.snippets.list(), client.snippets.delete, run_prefix)
    _delete_matching(client.credentials.list(), client.credentials.delete, run_prefix)
    _delete_matching(client.alerts.list_rules(), client.alerts.delete_rule, run_prefix)


def _delete_matching(items: Any, delete: Callable[[str], Any], run_prefix: str) -> None:
    for item in items:
        data = item if isinstance(item, dict) else item.to_dict()
        if str(data.get("name", "")).startswith(run_prefix):
            with contextlib.suppress(NotFoundError):
                delete(str(data["id"]))
