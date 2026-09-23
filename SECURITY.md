# Security Policy

## Modelo de ameacas

O termix-mcp fala com o Termix usando uma unica API key (`TERMIX_API_KEY`). O que essa
API key pode fazer no Termix, o termix-mcp tambem pode fazer atraves de um agente LLM -
o servidor nao adiciona uma segunda barreira de autorizacao alem do RBAC do proprio
Termix. Consequencias praticas:

- **Use uma API key dedicada, com RBAC minimo.** Se o agente so precisa ver hosts e
  rodar snippets, a key nao deveria ter acesso a `credentials`, `admin` nem a hosts fora
  do escopo pretendido. O Termix aplica RBAC por API key; o termix-mcp nao filtra por
  cima disso, so oferece toolsets/read-only como uma segunda camada opcional.
- **`TERMIX_MCP_READ_ONLY=true`** bloqueia toda tool de escrita em duas camadas
  (nao aparece na listagem e e rejeitada se chamada mesmo assim). Use quando o caso de
  uso e so leitura/diagnostico.
- **Toolsets fora do default sao opt-in por motivo.** `credentials` expoe segredos
  (via `termix_reveal_*`, quando `TERMIX_MCP_REDACT_SECRETS=false`); `files`/`docker`
  abrem uma sessao SSH real no host de destino; `admin`/`dangerous` tocam configuracao
  da instancia. Ligue so o que o caso de uso pedir.
- **Redacao por padrao.** Campos que parecem segredo (senha, chave privada, token,
  TOTP, API key) saem mascarados (`***`) em toda saida de tool, a menos que a tool seja
  explicitamente de revelacao e `TERMIX_MCP_REDACT_SECRETS=false`. Isso e uma heuristica
  por nome de campo, nao uma garantia formal - nao e substituto para RBAC correto na API
  key.
- **Prompt injection via conteudo do Termix e risco do operador.** Nome de host,
  descricao de snippet, log de sessao etc. sao texto que um agente pode ler e agir sobre.
  Trate o conteudo do seu Termix como voce trataria qualquer entrada nao confiavel para
  o agente.
- **Sem execucao de shell arbitrario na v1.** Nenhuma tool aceita um comando livre para
  rodar num host; `termix_run_snippet` roda um snippet ja cadastrado no Termix, sujeito
  ao RBAC da API key.

## Transporte HTTP

O transporte HTTP (`TERMIX_MCP_TRANSPORT=http`) nao tem autenticacao propria na v1: ele
depende de bind local (`127.0.0.1` por padrao) e de um path aleatorio nao documentado
(`TERMIX_MCP_HTTP_PATH`, gerado e logado na inicializacao se nao for definido). Expor
isso além de localhost sem um reverse proxy com autenticacao na frente esta fora do
modelo de ameacas suportado.

## Fora de escopo

- Seguranca do proprio Termix (autenticacao, RBAC, armazenamento de segredos) - reporte
  no [repositorio do Termix](https://github.com/LukeGus/Termix).
- Vulnerabilidades no `termix-sdk` - reporte no
  [repositorio do SDK](https://github.com/sujirodev/termix-sdk).

## Reportando uma vulnerabilidade

Abra um [GitHub Security Advisory](https://github.com/sujirodev/termix-mcp/security/advisories/new) privado neste repositorio. Nao abra uma issue publica para uma vulnerabilidade ainda nao corrigida.
