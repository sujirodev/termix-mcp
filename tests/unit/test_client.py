from __future__ import annotations

from termix_sdk import AsyncTermixClient

from termix_mcp.client import build_client


def test_build_client_passes_settings_through(make_settings) -> None:
    settings = make_settings(
        TERMIX_URL="https://termix.example.com",
        TERMIX_API_KEY="tmx_testkey",
        TERMIX_VERIFY_SSL="false",
        TERMIX_TIMEOUT="10",
        TERMIX_MAX_RETRIES="5",
    )

    client = build_client(settings)

    assert isinstance(client, AsyncTermixClient)
    assert client.hosts is not None  # constructed without error, resources wired up


def test_build_client_omits_empty_service_urls(make_settings) -> None:
    settings = make_settings()
    client = build_client(settings)
    assert isinstance(client, AsyncTermixClient)
