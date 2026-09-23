## O que muda

<!-- Uma ou duas frases. Link para a issue, se houver. -->

## Checklist

- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy src tests`
- [ ] `uv run pytest -q` (unit + contrato) verde
- [ ] Tool nova ou alterada: entrada na tabela do README regenerada (`scripts/generate_tool_docs.py`) e snapshot de contrato atualizado (`pytest tests/contract --snapshot-update`) de proposito
- [ ] Bug corrigido: teste de regressao incluido
- [ ] Testado com um agente LLM (Claude Code, Claude Desktop, Cursor...): qual, e o que voce pediu a ele

## Testado com um agente

<!-- Ex.: "Claude Code, 'lista meus hosts da pasta prod e mostra as metricas do primeiro'". -->
