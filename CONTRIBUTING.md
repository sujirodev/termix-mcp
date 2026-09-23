# Contribuindo

## Setup

```bash
uv sync --group dev
```

## Comandos

```bash
uv run ruff check .          # lint
uv run ruff format .         # formata
uv run mypy src tests        # tipos (strict)
uv run pytest -q             # unit + contrato (tests/e2e/ e pulado sem TERMIX_E2E=1)
uv run pytest tests/contract --snapshot-update   # tool nova/alterada: regrava o snapshot do catalogo
TERMIX_E2E=1 uv run pytest tests/e2e -m "e2e and not requires_ssh" -q   # sobe docker/e2e/compose.yml sozinho
TERMIX_E2E=1 TERMIX_E2E_BASE_URL=http://localhost:8080 uv run pytest tests/e2e -q  # contra um Termix ja rodando
uv build --wheel && docker build -t termix-mcp .   # imagem local (instala o wheel de dist/)
uv run python scripts/generate_tool_docs.py         # regenera a tabela do README
uv run python scripts/generate_tool_docs.py --check # verifica se esta desatualizada (CI)
```

## Adicionar uma tool nova

1. Confirme o metodo do `termix-sdk` lendo o codigo em `.venv/Lib/site-packages/termix_sdk/resources/` (ou `site-packages` equivalente) - nao assuma nome de metodo pelo `CHANGELOG.md` do SDK, ele muda entre versoes.
2. Escreva a tool em `src/termix_mcp/tools/tools_<dominio>.py`, dentro de `register_<dominio>_tools(mcp, client, settings)`, decorada com `@guarded(mcp, settings, toolset=..., read_only=..., destructive=..., idempotent=..., flags=...)`.
3. Parametros com `Annotated[tipo, Field(description=...)]`; sem `Any` solto no retorno de topo.
4. Passe o retorno por `shaping.simplify`/`simplify_dict` e, se puder conter segredo, por `redaction.redact`.
5. Erros do SDK nao precisam de tratamento manual - `@guarded` ja mapeia `TermixError` para `ToolError`; so trate um erro especifico se a mensagem generica de `errors.py` nao for acionavel.
6. Teste unitario em `tests/unit/tools/test_tools_<dominio>.py`: pelo menos o caminho feliz de cada tool nova, mais 1 erro se o modulo ainda nao tiver teste de erro.
7. Rode `uv run python scripts/generate_tool_docs.py` e confirme a tool nova na tabela do README; rode `uv run pytest tests/contract --snapshot-update` e revise o diff de `tests/contract/catalog_snapshot.json` (e o contrato publico da tool).
7b. Se a tool nao precisa de SSH real, adicione um caso em `tests/e2e/test_tools_e2e.py`; se precisa, marque com `@pytest.mark.requires_ssh` (so o `live.yml` semanal roda).
8. Teste manualmente com um agente (Claude Code, Claude Desktop) pelo menos uma vez antes de abrir o PR; anote no PR o que voce mandou o agente fazer.

## Politica de testes

- Bug corrigido exige teste de regressao.
- Tool nova exige teste unitario (mock do client); E2E fica para quando `tests/e2e/` tiver fixtures para o dominio.
- Mudanca em `policy.py`, `redaction.py` ou `config.py` exige teste cobrindo o caso que motivou a mudanca.

## Commits e PRs

[Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) - o changelog e gerado a partir disso.

PRs sem atividade por 7 dias sao marcados como abandonados e podem ser fechados.
