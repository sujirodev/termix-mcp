# Security Policy

## Threat model

termix-mcp talks to Termix using a single API key (`TERMIX_API_KEY`). Whatever that
API key can do in Termix, termix-mcp can also do through an LLM agent -
the server doesn't add a second authorization barrier beyond Termix's own RBAC.
Practical consequences:

- **Use a dedicated API key with minimal RBAC.** If the agent only needs to view hosts and
  run snippets, the key shouldn't have access to `credentials`, `admin`, or hosts outside
  the intended scope. Termix enforces RBAC per API key; termix-mcp doesn't filter on top
  of that, it only offers toolsets/read-only as an optional second layer.
- **`TERMIX_MCP_READ_ONLY=true`** blocks every write tool at two layers
  (it doesn't appear in the listing and is rejected if called anyway). Use it when the
  use case is read-only/diagnostics.
- **Toolsets outside the default are opt-in for a reason.** `credentials` exposes secrets
  (via `termix_reveal_*`, when `TERMIX_MCP_REDACT_SECRETS=false`); `files`/`docker`
  open a real SSH session on the target host; `admin`/`dangerous` touch instance
  configuration. Only enable what the use case requires.
- **Redaction by default.** Fields that look like secrets (password, private key, token,
  TOTP, API key) come out masked (`***`) in every tool output, unless the tool is
  explicitly a reveal tool and `TERMIX_MCP_REDACT_SECRETS=false`. This is a heuristic
  based on field name, not a formal guarantee - it's not a substitute for correct RBAC on the API
  key.
- **Prompt injection via Termix content is the operator's risk.** Host names,
  snippet descriptions, session logs, etc. are text that an agent can read and act on.
  Treat your Termix content as you would treat any untrusted input given to
  the agent.
- **No arbitrary shell execution in v1.** No tool accepts a free-form command to
  run on a host; `termix_run_snippet` runs a snippet already registered in Termix, subject
  to the API key's RBAC.

## HTTP transport

The HTTP transport (`TERMIX_MCP_TRANSPORT=http`) has no authentication of its own in v1: it
relies on a local bind (`127.0.0.1` by default) and an undocumented random path
(`TERMIX_MCP_HTTP_PATH`, generated and logged at startup if not set). Exposing
this beyond localhost without an authenticating reverse proxy in front is outside the
supported threat model.

## Out of scope

- Security of Termix itself (authentication, RBAC, secret storage) - report it
  at the [Termix repository](https://github.com/LukeGus/Termix).
- Vulnerabilities in `termix-sdk` - report them at the
  [SDK repository](https://github.com/sujirodev/termix-sdk).

## Reporting a vulnerability

Open a private [GitHub Security Advisory](https://github.com/sujirodev/termix-mcp/security/advisories/new) in this repository. Don't open a public issue for an unfixed vulnerability.
