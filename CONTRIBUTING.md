# Contributing

## Setup

```bash
uv sync --group dev
```

## Commands

```bash
uv run ruff check .          # lint
uv run ruff format .         # format
uv run mypy src tests        # types (strict)
uv run pytest -q             # unit + contract (tests/e2e/ is skipped without TERMIX_E2E=1)
uv run pytest tests/contract --snapshot-update   # new/changed tool: rewrites the catalog snapshot
TERMIX_E2E=1 uv run pytest tests/e2e -m "e2e and not requires_ssh" -q   # spins up docker/e2e/compose.yml on its own
TERMIX_E2E=1 TERMIX_E2E_BASE_URL=http://localhost:8080 uv run pytest tests/e2e -q  # against an already-running Termix
uv build --wheel && docker build -t termix-mcp .   # local image (installs the wheel from dist/)
uv run python scripts/generate_tool_docs.py         # regenerates the README table
uv run python scripts/generate_tool_docs.py --check # checks if it's out of date (CI)
```

## Adding a new tool

1. Confirm the `termix-sdk` method by reading the code in `.venv/Lib/site-packages/termix_sdk/resources/` (or the equivalent `site-packages`) - don't assume a method name from the SDK's `CHANGELOG.md`, it changes between versions.
2. Write the tool in `src/termix_mcp/tools/tools_<domain>.py`, inside `register_<domain>_tools(mcp, client, settings)`, decorated with `@guarded(mcp, settings, toolset=..., read_only=..., destructive=..., idempotent=..., flags=...)`.
3. Parameters with `Annotated[type, Field(description=...)]`; no bare `Any` in the top-level return.
4. Pass the return through `shaping.simplify`/`simplify_dict` and, if it might contain a secret, through `redaction.redact`.
5. SDK errors don't need manual handling - `@guarded` already maps `TermixError` to `ToolError`; only handle a specific error if the generic message in `errors.py` isn't actionable.
6. Unit test in `tests/unit/tools/test_tools_<domain>.py`: at least the happy path for each new tool, plus 1 error case if the module doesn't have an error test yet.
7. Run `uv run python scripts/generate_tool_docs.py` and confirm the new tool appears in the README table; run `uv run pytest tests/contract --snapshot-update` and review the diff of `tests/contract/catalog_snapshot.json` (it's the tool's public contract).
7b. If the tool doesn't need a real SSH connection, add a case in `tests/e2e/test_tools_e2e.py`; if it does, mark it with `@pytest.mark.requires_ssh` (only the weekly `live.yml` runs it).
8. Manually test with an agent (Claude Code, Claude Desktop) at least once before opening the PR; note in the PR what you had the agent do.

## Testing policy

- A fixed bug requires a regression test.
- A new tool requires a unit test (mocked client); E2E is reserved for when `tests/e2e/` has fixtures for the domain.
- A change to `policy.py`, `redaction.py`, or `config.py` requires a test covering the case that motivated the change.

## Commits and PRs

[Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) - the changelog is generated from these.

PRs with no activity for 7 days are marked as stale and may be closed.
