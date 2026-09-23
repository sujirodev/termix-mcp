# Build the wheel first (`uv build`); the image installs it instead of building from
# source so uv-dynamic-versioning sees the git tag at build time, not inside Docker.
#
#   uv build && docker build -t termix-mcp .
#   docker run --rm -e TERMIX_URL=... -e TERMIX_API_KEY=... termix-mcp

FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.9 /uv /usr/local/bin/uv
WORKDIR /build
COPY dist/*.whl ./
RUN uv venv /opt/venv && uv pip install --python /opt/venv/bin/python --no-cache ./*.whl

FROM python:3.13-slim
LABEL org.opencontainers.image.source="https://github.com/sujirodev/termix-mcp" \
      org.opencontainers.image.licenses="MIT" \
      io.modelcontextprotocol.server.name="io.github.sujirodev/termix-mcp"
RUN useradd --system --uid 10001 --create-home termix
COPY --from=builder /opt/venv /opt/venv
USER termix
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    TERMIX_MCP_HTTP_HOST=0.0.0.0
EXPOSE 8765
ENTRYPOINT ["termix-mcp"]
