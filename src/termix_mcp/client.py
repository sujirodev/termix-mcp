from __future__ import annotations

from termix_sdk import AsyncTermixClient

from termix_mcp.config import Settings


def build_client(settings: Settings) -> AsyncTermixClient:
    return AsyncTermixClient(
        base_url=settings.termix_url,
        api_key=settings.termix_api_key,
        service_urls=settings.termix_service_urls or None,
        timeout=settings.termix_timeout,
        verify=settings.termix_verify_ssl,
        max_network_retries=settings.termix_max_retries,
    )
