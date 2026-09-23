from __future__ import annotations

import sys

from pydantic import ValidationError

from termix_mcp import __version__
from termix_mcp.config import Settings
from termix_mcp.server import build_server, configure_logging


def run() -> None:
    if "--version" in sys.argv[1:]:
        print(f"termix-mcp {__version__}")
        return

    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        print(f"Configuracao invalida:\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    configure_logging(settings)
    mcp = build_server(settings)

    if settings.mcp_transport == "http":
        mcp.run(
            transport="http",
            host=settings.mcp_http_host,
            port=settings.mcp_http_port,
            path=f"/{settings.resolved_http_path}",
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
