from __future__ import annotations

from fastmcp.exceptions import ToolError
from termix_sdk import (
    APIConnectionError,
    AuthenticationError,
    DataLockedError,
    NotFoundError,
    RateLimitError,
    ServerError,
    SessionExpiredError,
    TOTPRequiredError,
)
from termix_sdk import (
    PermissionError as TermixPermissionError,
)

from termix_mcp.errors import to_tool_error


def test_totp_required_maps_to_actionable_message() -> None:
    err = to_tool_error(TOTPRequiredError("totp needed"))
    assert isinstance(err, ToolError)
    assert "API key" in str(err)


def test_session_expired_mentions_api_key() -> None:
    err = to_tool_error(SessionExpiredError("session gone"))
    assert "API key" in str(err) or "TERMIX_API_KEY" in str(err)


def test_rate_limit_includes_remaining_time() -> None:
    err = to_tool_error(RateLimitError("too many", remaining_time=42.0))
    assert "42" in str(err)


def test_rate_limit_without_remaining_time_still_actionable() -> None:
    err = to_tool_error(RateLimitError("too many"))
    assert "requisi" in str(err).lower()


def test_permission_error_mentions_rbac() -> None:
    err = to_tool_error(TermixPermissionError("nope"))
    assert "RBAC" in str(err) or "permiss" in str(err).lower()


def test_not_found_mentions_resource() -> None:
    err = to_tool_error(NotFoundError("missing"))
    assert "encontrado" in str(err).lower()


def test_data_locked_mentions_unlock() -> None:
    err = to_tool_error(DataLockedError("locked"))
    assert "bloqueado" in str(err).lower()


def test_connection_error_mentions_url() -> None:
    err = to_tool_error(APIConnectionError("dns fail"))
    assert "TERMIX_URL" in str(err)


def test_generic_401_mentions_api_key() -> None:
    err = to_tool_error(AuthenticationError("bad creds", http_status=401))
    assert "API key" in str(err)


def test_server_error_includes_status() -> None:
    err = to_tool_error(ServerError("boom", http_status=500))
    assert "500" in str(err)
