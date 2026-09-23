"""Settings loaded from environment variables. Validates eagerly so startup fails fast
with a clear message instead of failing on the first tool call.
"""

from __future__ import annotations

import logging
import secrets
from typing import Literal

from pydantic import Field, PrivateAttr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from termix_mcp.tools.toolsets import resolve_toolsets

logger = logging.getLogger("termix_mcp.config")


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=True, extra="ignore")

    # Cliente Termix (AsyncTermixClient)
    termix_url: str = Field(alias="TERMIX_URL")
    termix_api_key: str = Field(alias="TERMIX_API_KEY")
    termix_service_urls: dict[str, str] = Field(default_factory=dict, alias="TERMIX_SERVICE_URLS")
    termix_verify_ssl: bool = Field(default=True, alias="TERMIX_VERIFY_SSL")
    termix_timeout: float = Field(default=30.0, alias="TERMIX_TIMEOUT")
    termix_max_retries: int = Field(default=2, alias="TERMIX_MAX_RETRIES")

    # Politica do MCP
    mcp_read_only: bool = Field(default=False, alias="TERMIX_MCP_READ_ONLY")
    mcp_toolsets_raw: str = Field(default="default", alias="TERMIX_MCP_TOOLSETS")
    mcp_enabled_tools_raw: str = Field(default="", alias="TERMIX_MCP_ENABLED_TOOLS")
    mcp_disabled_tools_raw: str = Field(default="", alias="TERMIX_MCP_DISABLED_TOOLS")
    mcp_redact_secrets: bool = Field(default=True, alias="TERMIX_MCP_REDACT_SECRETS")
    mcp_max_items: int = Field(default=50, alias="TERMIX_MCP_MAX_ITEMS")

    # Transporte
    mcp_transport: Literal["stdio", "http"] = Field(default="stdio", alias="TERMIX_MCP_TRANSPORT")
    mcp_http_host: str = Field(default="127.0.0.1", alias="TERMIX_MCP_HTTP_HOST")
    mcp_http_port: int = Field(default=8765, alias="TERMIX_MCP_HTTP_PORT")
    mcp_http_path: str | None = Field(default=None, alias="TERMIX_MCP_HTTP_PATH")

    mcp_log_level: str = Field(default="INFO", alias="TERMIX_MCP_LOG_LEVEL")

    _toolsets: frozenset[str] = PrivateAttr()
    _enabled_tools: frozenset[str] = PrivateAttr()
    _disabled_tools: frozenset[str] = PrivateAttr()
    _resolved_http_path: str | None = PrivateAttr(default=None)

    @field_validator("termix_url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError(
                f"TERMIX_URL precisa comecar com http:// ou https://, recebido: {value!r}"
            )
        return value.rstrip("/")

    @field_validator("termix_api_key")
    @classmethod
    def _validate_api_key(cls, value: str) -> str:
        if not value.startswith("tmx_"):
            raise ValueError(
                "TERMIX_API_KEY precisa comecar com 'tmx_' (JWT/TOTP nao sao suportados "
                "pelo termix-mcp)."
            )
        return value

    @model_validator(mode="after")
    def _resolve_derived_fields(self) -> Settings:
        requested = set(_split_csv(self.mcp_toolsets_raw))
        try:
            toolsets = resolve_toolsets(requested)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        self._toolsets = toolsets
        self._enabled_tools = frozenset(_split_csv(self.mcp_enabled_tools_raw))
        self._disabled_tools = frozenset(_split_csv(self.mcp_disabled_tools_raw))

        http_path = self.mcp_http_path
        if self.mcp_transport == "http" and not http_path:
            http_path = secrets.token_urlsafe(24)
            logger.warning(
                "TERMIX_MCP_HTTP_PATH nao definido; gerado aleatoriamente para esta "
                "execucao: /%s (nao sera o mesmo na proxima inicializacao)",
                http_path,
            )
        self._resolved_http_path = http_path
        return self

    @property
    def toolsets(self) -> frozenset[str]:
        return self._toolsets

    @property
    def enabled_tools(self) -> frozenset[str]:
        return self._enabled_tools

    @property
    def disabled_tools(self) -> frozenset[str]:
        return self._disabled_tools

    @property
    def resolved_http_path(self) -> str | None:
        return self._resolved_http_path
