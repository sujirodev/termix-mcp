from __future__ import annotations

import pytest
from pydantic import ValidationError

from termix_mcp.config import Settings


def test_minimal_config_has_default_toolsets(make_settings) -> None:
    settings = make_settings()
    assert settings.toolsets == {"hosts", "snippets", "dashboard", "metrics", "system", "audit"}
    assert settings.mcp_read_only is False
    assert settings.mcp_transport == "stdio"


def test_url_without_scheme_fails(make_settings) -> None:
    with pytest.raises(ValidationError, match="http"):
        make_settings(TERMIX_URL="termix.example.com")


def test_url_trailing_slash_is_stripped(make_settings) -> None:
    settings = make_settings(TERMIX_URL="https://termix.example.com/")
    assert settings.termix_url == "https://termix.example.com"


def test_api_key_without_prefix_fails(make_settings) -> None:
    with pytest.raises(ValidationError, match="tmx_"):
        make_settings(TERMIX_API_KEY="not-a-key")


def test_unknown_toolset_fails(make_settings) -> None:
    with pytest.raises(ValidationError, match="desconhecido"):
        make_settings(TERMIX_MCP_TOOLSETS="hosts,not-a-toolset")


def test_toolsets_all_excludes_admin_and_dangerous(make_settings) -> None:
    settings = make_settings(TERMIX_MCP_TOOLSETS="all")
    assert "admin" not in settings.toolsets
    assert "dangerous" not in settings.toolsets
    assert "files" in settings.toolsets


def test_toolsets_admin_requires_explicit_name(make_settings) -> None:
    settings = make_settings(TERMIX_MCP_TOOLSETS="hosts,admin")
    assert settings.toolsets == {"hosts", "admin"}


def test_enabled_disabled_tools_parsed_as_csv(make_settings) -> None:
    settings = make_settings(
        TERMIX_MCP_ENABLED_TOOLS="termix_list_hosts, termix_get_host",
        TERMIX_MCP_DISABLED_TOOLS="termix_delete_host",
    )
    assert settings.enabled_tools == {"termix_list_hosts", "termix_get_host"}
    assert settings.disabled_tools == {"termix_delete_host"}


def test_http_path_generated_when_missing(make_settings) -> None:
    settings = make_settings(TERMIX_MCP_TRANSPORT="http")
    assert settings.resolved_http_path
    assert settings.mcp_http_path is None  # raw field untouched; only the resolved copy is set


def test_http_path_kept_when_provided(make_settings) -> None:
    settings = make_settings(TERMIX_MCP_TRANSPORT="http", TERMIX_MCP_HTTP_PATH="my-secret-path")
    assert settings.resolved_http_path == "my-secret-path"


def test_stdio_transport_does_not_generate_http_path(make_settings) -> None:
    settings = make_settings()
    assert settings.resolved_http_path is None


def test_service_urls_parsed_from_json(monkeypatch) -> None:
    # Complex-type JSON parsing only happens for real env vars, not constructor kwargs
    # (pydantic-settings' EnvSettingsSource vs. InitSettingsSource) - use monkeypatch here.
    monkeypatch.setenv("TERMIX_URL", "https://termix.example.com")
    monkeypatch.setenv("TERMIX_API_KEY", "tmx_testkey")
    monkeypatch.setenv("TERMIX_SERVICE_URLS", '{"database": "http://localhost:8081"}')
    settings = Settings()  # type: ignore[call-arg]
    assert settings.termix_service_urls == {"database": "http://localhost:8081"}
