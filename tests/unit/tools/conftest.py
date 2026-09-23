from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastmcp import FastMCP


@pytest.fixture
def mock_client() -> MagicMock:
    """A duck-typed stand-in for AsyncTermixClient: `mock_client.hosts.list = AsyncMock(...)`
    etc. Not spec'd against the real class (its resource attributes are set at instance
    __init__ time, so `create_autospec` can't see them) - tests set up exactly the calls
    they exercise."""
    return MagicMock()


@pytest.fixture
def build_mcp(
    mock_client: MagicMock, make_settings: Callable[..., Any]
) -> Callable[..., tuple[FastMCP, Any]]:
    def _build(
        register_fn: Callable[..., None], **settings_overrides: object
    ) -> tuple[FastMCP, Any]:
        mcp = FastMCP()
        settings = make_settings(**settings_overrides)
        register_fn(mcp, mock_client, settings)
        return mcp, settings

    return _build


@pytest.fixture
def patch_ssh_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replaces `async_ssh_session` in tools_files/tools_docker with a stub that just
    yields the wrapped service unchanged - tests set methods directly on
    `mock_client.file_manager`/`mock_client.docker` instead of re-testing the SDK's own
    connect/disconnect/session-id-injection plumbing (that's the SDK's test suite's job)."""

    @asynccontextmanager
    async def _fake_session(service: Any, *, host_id: Any, **kwargs: Any) -> Any:
        yield service

    monkeypatch.setattr("termix_mcp.tools.tools_files.async_ssh_session", _fake_session)
    monkeypatch.setattr("termix_mcp.tools.tools_docker.async_ssh_session", _fake_session)
