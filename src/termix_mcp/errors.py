"""Maps termix_sdk.TermixError subclasses to fastmcp.ToolError with an actionable message.

Order matters: isinstance checks below go from most specific to least specific subclass,
mirroring termix_sdk's own hierarchy (TOTPRequiredError/SessionExpiredError extend
AuthenticationError; every APIStatusError subclass extends APIStatusError extends
TermixError).
"""

from __future__ import annotations

from fastmcp.exceptions import ToolError
from termix_sdk import (
    APIConnectionError,
    DataLockedError,
    NotFoundError,
    RateLimitError,
    SessionExpiredError,
    TermixError,
    TOTPRequiredError,
)
from termix_sdk import (
    PermissionError as TermixPermissionError,
)


def to_tool_error(exc: TermixError) -> ToolError:
    if isinstance(exc, TOTPRequiredError):
        return ToolError(
            "Autenticacao com TOTP nao e suportada pelo termix-mcp. Use uma API key "
            "(tmx_...) em vez de login por usuario/senha."
        )
    if isinstance(exc, SessionExpiredError):
        return ToolError(
            "Sessao expirada ou invalida. O termix-mcp usa API key, nao sessao de "
            "usuario; verifique TERMIX_API_KEY."
        )
    if isinstance(exc, RateLimitError):
        wait = f" Tente novamente em {exc.remaining_time:.0f}s." if exc.remaining_time else ""
        return ToolError(f"Limite de requisicoes do Termix atingido.{wait}")
    if isinstance(exc, TermixPermissionError):
        return ToolError(
            "A API key nao tem permissao para esta operacao no Termix (RBAC). Peca ao "
            f"administrador para conceder o escopo necessario. Detalhe: {exc.user_message}"
        )
    if isinstance(exc, NotFoundError):
        return ToolError(f"Recurso nao encontrado no Termix: {exc.user_message}")
    if isinstance(exc, DataLockedError):
        return ToolError(
            "Os dados do Termix estao bloqueados (instancia ainda nao foi desbloqueada "
            "apos reiniciar). Desbloqueie a instancia antes de tentar de novo."
        )
    if isinstance(exc, APIConnectionError):
        return ToolError(
            f"Nao foi possivel conectar ao Termix em TERMIX_URL: {exc.user_message}. "
            "Verifique a URL e se o Termix esta no ar."
        )
    # AuthenticationError (generic 401), InvalidRequestError, ServerError and any other
    # APIStatusError fall through to a generic-but-still-actionable message.
    status = getattr(exc, "http_status", None)
    if status == 401:
        return ToolError(f"API key invalida ou expirada: {exc.user_message}")
    return ToolError(f"Erro do Termix (status={status}): {exc.user_message}")
