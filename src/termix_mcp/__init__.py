from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("termix-mcp")
except PackageNotFoundError:  # pacote nao instalado (ex.: rodando dos fontes sem build)
    __version__ = "0.0.0+dev"
