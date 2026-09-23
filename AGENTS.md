# AGENTS.md

Guia para agentes de codigo (Claude Code e similares) trabalhando neste repositorio.

## O que e

`termix-mcp`: servidor MCP em Python sobre o [`termix-sdk`](https://github.com/sujirodev/termix-sdk), expondo um conjunto curado de tools para operar um [Termix](https://github.com/LukeGus/Termix) self-hosted. Nao e um wrapper 1:1 da API - toda tool nova precisa de justificativa (ver `docs/plano-implementacao.md` secao 6).

## Arquitetura

```
src/termix_mcp/
  server.py        monta o FastMCP, aplica lifespan (fecha o client no shutdown)
  config.py        Settings (pydantic-settings), valida tudo na inicializacao
  client.py        constroi AsyncTermixClient a partir de Settings
  errors.py        TermixError -> ToolError com mensagem acionavel
  redaction.py      mascara campos que parecem segredo (heuristica por nome de campo)
  policy.py        @guarded: registra metadado, aplica read-only (2 camadas), mapeia erro, loga
  shaping.py       simplify/simplify_dict: TermixObject -> dict enxuto, paginacao
  tools/
    registry.py    descobre tools_*.py via pkgutil, chama register_<dominio>_tools
    toolsets.py    taxonomia de toolsets + TOOL_TABLE (tool -> toolset/flags/hints)
    tools_*.py     uma tool = uma funcao async decorada com @guarded
  resources/
    server_info.py termix://server/info (diagnostico)
```

## Comandos

```bash
uv sync --group dev
uv run ruff check . && uv run ruff format --check .
uv run mypy src tests
uv run pytest -q
uv run python scripts/generate_tool_docs.py --check
```

## Convencoes

- **Nunca adivinhe um metodo do SDK.** Leia o codigo real em
  `.venv/Lib/site-packages/termix_sdk/resources/<modulo>.py` antes de chamar
  `client.<modulo>.<metodo>()`. O `CHANGELOG.md` do SDK e referencia de leitura, nao
  fonte de verdade sobre o que existe na versao instalada.
- **Toda tool passa por `@guarded`.** E o unico jeito de: (1) aparecer em
  `toolsets.TOOL_TABLE` (testado: toda tool registrada precisa estar la e vice-versa),
  (2) respeitar read-only nas duas camadas, (3) ter erro do SDK mapeado para `ToolError`.
  Nunca registre uma tool direto em `mcp.tool()` sem passar por `guarded`.
- **Toda saida passa por `shaping.simplify`/`simplify_dict`.** Converte `TermixObject`
  em dict, corta ruido, pagina listas grandes (`items`/`total`/`truncated`).
- **Redacao e defesa em profundidade, nao substituta de RBAC.** `redaction.redact` mascara
  por heuristica de nome de campo; a garantia real de "o agente nao pode ver X" vem do
  RBAC da API key no Termix, nao do MCP.
- **Nomes de tool**: `termix_<verbo>_<recurso>`, snake_case (`termix_list_hosts`).
- **Nunca**: tool sem annotations (`read_only_hint`/`destructive_hint`/`idempotent_hint`),
  tool que nao esta na tabela gerada do README, segredo em log (o log de `policy.py` so
  registra nome da tool, duracao e classe do erro - nunca argumentos).
- **Sessoes SSH** (`files`, `docker`, quando implementados): sessao por chamada via
  `termix_sdk.async_ssh_session`, aberta e fechada dentro da tool. Nenhuma tool aceita
  comando shell arbitrario.

## Toolsets

Default (sempre ligados): `hosts`, `snippets`, `dashboard`, `metrics`, `system`, `audit`.
Opt-in (`TERMIX_MCP_TOOLSETS=...`): `credentials`, `files`, `docker`, `tunnels`, `alerts`,
`automations`, `users`. Explicitos, fora de `all`: `admin`, `dangerous`.

## FastMCP 4.x - pontos que a API real exige (validado contra `fastmcp==4.0.5`)

- `mcp.tool(name=..., annotations=ToolAnnotations(read_only_hint=..., destructive_hint=...,
  idempotent_hint=..., open_world_hint=...), tags={...})(fn)` - os nomes dos campos de
  `ToolAnnotations` sao `snake_case` no construtor Python (`mcp.types.ToolAnnotations`),
  mesmo virando `readOnlyHint` no protocolo.
- Nao ha filtro nativo de tools por tag no FastMCP 4.x (`include_tags`/`exclude_tags`
  nao existem) - o filtro por toolset acontece em `registry.py`/`policy.py`, decidindo
  se `mcp.tool()` e chamado, nao em runtime via tags do FastMCP.
- Lifespan: `FastMCP(lifespan=<async contextmanager que recebe o app e faz yield>)`;
  o client e construido antes (sincrono, sem I/O) e fechado no `finally` do lifespan.
- `mcp.call_tool(name, args)` levanta `ToolError` diretamente (nao devolve um resultado
  de erro) - e assim que os testes verificam mapeamento de erro.

## Testes

`tests/unit/` cobre config/errors/redaction/shaping/policy/registry/server e cada
`tools_*.py` com um client mockado (`unittest.mock.MagicMock`, sem `spec=` porque
`AsyncTermixClient` seta seus atributos de recurso em `__init__`, nao na classe).
`tests/unit/test_policy_sweep.py` varre o catalogo inteiro: default nunca expoe
`admin`/`data-access`/`dangerous`; read-only nunca expoe uma write tool.
`tests/contract/` valida cada input schema como JSON Schema e compara o catalogo com
`catalog_snapshot.json` (mudou uma tool -> `pytest tests/contract --snapshot-update`).
`tests/e2e/` roda tudo contra um Termix real (`TERMIX_E2E=1`; sobe
`docker/e2e/compose.yml` sozinho); `files`/`docker` sao `requires_ssh` (so `live.yml`).

## Release

Tag `vX.Y.Z` -> `release.yml`: git-cliff gera as notas, CI completo, PyPI (trusted
publishing, aprovacao manual no environment `pypi`), GitHub Release, GHCR
(`docker.yml`), MCP Registry (`server.json`, versao carimbada por `jq`; nunca falha o
release). Versao vem da tag via `uv-dynamic-versioning`; nao ha `__version__` hardcoded.
