# termix-mcp

[![CI](https://github.com/sujirodev/termix-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sujirodev/termix-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/termix-mcp?cacheSeconds=3600)](https://pypi.org/project/termix-mcp/)
[![License](https://img.shields.io/github/license/sujirodev/termix-mcp)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/termix-mcp?cacheSeconds=3600)](https://pypi.org/project/termix-mcp/)

Servidor [MCP](https://modelcontextprotocol.io) para o [Termix](https://github.com/LukeGus/Termix), o gerenciador self-hosted de SSH/RDP/VNC. Deixa um agente (Claude Desktop, Claude Code, Cursor, VS Code...) listar e operar hosts, snippets, dashboard, metricas e auditoria do seu Termix, construido sobre o [termix-sdk](https://github.com/sujirodev/termix-sdk).

Nao e um wrapper 1:1 da API do Termix: e um conjunto curado de tools, seguro por padrao (sem segredos, sem sessao SSH persistente, sem tools destrutivas fora de toolsets explicitos).

<!-- mcp-name: io.github.sujirodev/termix-mcp -->

[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.sujirodev%2Ftermix--mcp-blue)](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.sujirodev/termix-mcp)

## Instalar

```bash
uvx termix-mcp
```

Alternativas: `pip install termix-mcp` ou a imagem `ghcr.io/sujirodev/termix-mcp`.

Requer uma API key do Termix (`tmx_...`) com permissao RBAC minima para o que o agente vai fazer - veja [SECURITY.md](SECURITY.md).

## Configurar no cliente

Claude Desktop / Claude Code (`claude_desktop_config.json` ou `.mcp.json`):

```json
{
  "mcpServers": {
    "termix": {
      "command": "uvx",
      "args": ["termix-mcp"],
      "env": {
        "TERMIX_URL": "https://termix.example.com",
        "TERMIX_API_KEY": "tmx_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

Cursor / VS Code: mesmo formato, no arquivo de configuracao MCP de cada um.

## Voce diz / o que acontece

| Voce diz | O que a tool faz |
|---|---|
| "quais hosts eu tenho cadastrados?" | `termix_list_hosts` |
| "mostra as metricas do host X" | `termix_get_host_metrics` |
| "roda o snippet Y no host X" | `termix_run_snippet` (bloqueada em modo read-only) |
| "cria um host novo pra esse servidor" | `termix_create_host` (bloqueada em modo read-only) |
| "o que aconteceu de auditoria essa semana?" | `termix_list_audit_events` |

## Variaveis de ambiente

| Variavel | Default | Descricao |
|---|---|---|
| `TERMIX_URL` | obrigatoria | URL base do Termix |
| `TERMIX_API_KEY` | obrigatoria | API key `tmx_...` (JWT/TOTP nao sao suportados) |
| `TERMIX_SERVICE_URLS` | vazio | JSON `{"database": "http://..."}` para instalacoes sem proxy |
| `TERMIX_VERIFY_SSL` | `true` | Valida certificado TLS |
| `TERMIX_TIMEOUT` | `30` | Timeout por requisicao (s) |
| `TERMIX_MAX_RETRIES` | `2` | Repassado ao SDK |
| `TERMIX_MCP_READ_ONLY` | `false` | Esconde e bloqueia tools de escrita |
| `TERMIX_MCP_TOOLSETS` | `default` | `default`, `all`, ou lista `hosts,snippets,files` |
| `TERMIX_MCP_ENABLED_TOOLS` | vazio | Allowlist por nome de tool |
| `TERMIX_MCP_DISABLED_TOOLS` | vazio | Denylist por nome de tool |
| `TERMIX_MCP_REDACT_SECRETS` | `true` | Mascara segredos em todas as saidas |
| `TERMIX_MCP_MAX_ITEMS` | `50` | Limite default de itens em listagens |
| `TERMIX_MCP_TRANSPORT` | `stdio` | `stdio` ou `http` |
| `TERMIX_MCP_HTTP_HOST` / `_PORT` | `127.0.0.1` / `8765` | Bind do transporte HTTP |
| `TERMIX_MCP_HTTP_PATH` | gerado e logado | Path secreto do endpoint HTTP |
| `TERMIX_MCP_LOG_LEVEL` | `INFO` | Nivel de log (stderr no stdio, stdout no http) |

## Toolsets

Ligados por padrao: `hosts`, `snippets`, `dashboard`, `metrics`, `system`, `audit`.

Opt-in (`TERMIX_MCP_TOOLSETS=hosts,files,docker,...`): `credentials`, `files`, `docker`, `tunnels`, `alerts`, `automations`, `users`.

Desligados e explicitos (nunca entram em `all`): `admin`, `dangerous`.

`TERMIX_MCP_READ_ONLY=true` esconde e bloqueia toda tool que nao seja read-only, em qualquer toolset.

## Tools

<details>
<summary>Lista completa de tools (gerada por <code>scripts/generate_tool_docs.py</code>)</summary>

<!-- TOOLS_TABLE_START -->
| Tool | Toolset | Read-only | Destrutiva | Flags |
|---|---|:---:|:---:|---|
| `termix_get_audit_forwarding` | admin | sim | nao | admin |
| `termix_get_branding` | admin | sim | nao | admin |
| `termix_get_encryption_status` | admin | sim | nao | admin |
| `termix_get_host_defaults` | admin | sim | nao | admin |
| `termix_get_termix_id_status` | admin | sim | nao | admin |
| `termix_list_sso_providers` | admin | sim | nao | admin |
| `termix_update_branding` | admin | nao | nao | admin |
| `termix_acknowledge_alert_firing` | alerts | nao | nao | - |
| `termix_create_alert_rule` | alerts | nao | nao | - |
| `termix_delete_alert_rule` | alerts | nao | sim | - |
| `termix_list_alert_rules` | alerts | sim | nao | - |
| `termix_get_session_log` | audit | sim | nao | - |
| `termix_list_audit_events` | audit | sim | nao | - |
| `termix_list_session_logs` | audit | sim | nao | - |
| `termix_get_automation` | automations | sim | nao | - |
| `termix_list_automations` | automations | sim | nao | - |
| `termix_list_fleets` | automations | sim | nao | - |
| `termix_run_automation` | automations | nao | nao | data-access |
| `termix_create_credential` | credentials | nao | nao | - |
| `termix_delete_credential` | credentials | nao | sim | - |
| `termix_get_credential` | credentials | sim | nao | - |
| `termix_list_credentials` | credentials | sim | nao | - |
| `termix_reveal_credential` | credentials | sim | nao | data-access |
| `termix_update_credential` | credentials | nao | nao | - |
| `termix_get_dashboard_summary` | dashboard | sim | nao | - |
| `termix_get_homepage` | dashboard | sim | nao | - |
| `termix_list_open_tabs` | dashboard | sim | nao | - |
| `termix_list_workspaces` | dashboard | sim | nao | - |
| `termix_get_container` | docker | sim | nao | data-access |
| `termix_get_container_logs` | docker | sim | nao | data-access |
| `termix_get_container_stats` | docker | sim | nao | data-access |
| `termix_list_containers` | docker | sim | nao | data-access |
| `termix_restart_container` | docker | nao | nao | data-access |
| `termix_start_container` | docker | nao | nao | data-access |
| `termix_stop_container` | docker | nao | nao | data-access |
| `termix_create_folder` | files | nao | nao | data-access |
| `termix_delete_file` | files | nao | sim | data-access |
| `termix_list_files` | files | sim | nao | data-access |
| `termix_move_file` | files | nao | nao | data-access |
| `termix_read_file` | files | sim | nao | data-access |
| `termix_rename_file` | files | nao | nao | data-access |
| `termix_write_file` | files | nao | nao | data-access |
| `termix_create_host` | hosts | nao | nao | - |
| `termix_delete_host` | hosts | nao | sim | - |
| `termix_disable_host_autostart` | hosts | nao | nao | - |
| `termix_enable_host_autostart` | hosts | nao | nao | - |
| `termix_get_host` | hosts | sim | nao | - |
| `termix_get_network_topology` | hosts | sim | nao | - |
| `termix_list_host_folders` | hosts | sim | nao | - |
| `termix_list_host_tags` | hosts | sim | nao | - |
| `termix_list_hosts` | hosts | sim | nao | - |
| `termix_update_host` | hosts | nao | nao | - |
| `termix_get_host_metrics` | metrics | sim | nao | - |
| `termix_get_host_status` | metrics | sim | nao | - |
| `termix_get_metrics_history` | metrics | sim | nao | - |
| `termix_get_proxmox_stats` | metrics | sim | nao | - |
| `termix_list_active_alerts` | metrics | sim | nao | - |
| `termix_list_host_statuses` | metrics | sim | nao | - |
| `termix_create_snippet` | snippets | nao | nao | - |
| `termix_delete_snippet` | snippets | nao | sim | - |
| `termix_get_snippet` | snippets | sim | nao | - |
| `termix_list_snippets` | snippets | sim | nao | - |
| `termix_run_snippet` | snippets | nao | nao | - |
| `termix_update_snippet` | snippets | nao | nao | - |
| `termix_get_preferences` | system | sim | nao | - |
| `termix_get_system_info` | system | sim | nao | - |
| `termix_list_api_keys` | system | sim | nao | - |
| `termix_create_tunnel` | tunnels | nao | nao | data-access |
| `termix_delete_tunnel` | tunnels | nao | nao | data-access |
| `termix_get_tunnel` | tunnels | sim | nao | - |
| `termix_list_tunnel_presets` | tunnels | sim | nao | - |
| `termix_list_tunnels` | tunnels | sim | nao | - |
| `termix_assign_role` | users | nao | nao | admin |
| `termix_get_user` | users | sim | nao | admin |
| `termix_list_credential_access` | users | sim | nao | admin |
| `termix_list_folder_access` | users | sim | nao | admin |
| `termix_list_roles` | users | sim | nao | admin |
| `termix_list_users` | users | sim | nao | admin |

Total: 78 tools.
<!-- TOOLS_TABLE_END -->

</details>

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Seguranca

Veja [SECURITY.md](SECURITY.md) para o modelo de ameaças.

## Licenca

[MIT](LICENSE)
