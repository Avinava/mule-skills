# MCP servers

The skills are instruction-only workflows and run without any MCP server. Three pinned servers make
them sharper: two need no credentials, one needs an Anypoint login.

| Server and source | Pin | Role | Credentials |
| --- | --- | --- | --- |
| [`mule-build`](https://github.com/Avinava/mule-build) | [`@sfdxy/mule-build@2.2.0`](https://registry.npmjs.org/@sfdxy%2Fmule-build/2.2.0) | Validation, testing, packaging, local runtime, versioning, security checks | None |
| [`mule-lint`](https://github.com/Avinava/mule-lint) | [`@sfdxy/mule-lint@1.27.0`](https://registry.npmjs.org/@sfdxy%2Fmule-lint/1.27.0) | Canonical Mule standards, static analysis, and machine-readable guidance | None |
| [`anypoint-connect`](https://github.com/Avinava/anypoint-connect) | [`@sfdxy/anypoint-connect@0.11.1`](https://registry.npmjs.org/@sfdxy%2Fanypoint-connect/0.11.1) | Authorized logs, metrics, deployments, API management, Exchange, MQ, Object Store | Anypoint Platform login |

Each server has its own documentation, which is the place to look for command references, tool
catalogs, and per-host setup beyond what the skills need:

| Server | Documentation |
| --- | --- |
| `mule-build` | <https://avinava.github.io/mule-build/> |
| `mule-lint` | <https://avinava.github.io/mule-lint/> |
| `anypoint-connect` | <https://avinava.github.io/anypoint-connect/> |

Package links resolve to the exact registry version the checked-in configuration uses rather than an
unpinned latest release. Node.js `>=20.19.0` satisfies all three.

## Which skill uses which server

| Skill | `mule-build` | `mule-lint` | `anypoint-connect` |
| --- | --- | --- | --- |
| `mule-docs` | Inventory support | Optional | No |
| `mule-development` | Validation and tests after a change | Static analysis of changed files | No |
| `mule-testing` | Primary test execution and reports | Testing standards and guidance | No |
| `mule-troubleshooting` | Reproduction and validation | Optional | Telemetry for the incident window |
| `mule-ops` | No | No | Primary evidence source |
| `mule-review` | Validation during review | Static analysis | Optional runtime verification only |
| `mule-build` | Primary | Static and security gate | Only for authorized publish or deploy |

Nothing in this table is required. A missing server becomes a disclosed coverage gap, not a failed
workflow.

## Capabilities by server

**`mule-build`** — project readiness and resolved configuration, build and validation runs, local
runtime start, stop, and status, security enforcement and secure-property handling, and version and
release operations.

**`mule-lint`** — full-project lint analysis with machine-readable reports, rule detail lookup,
single-snippet validation, and Mule XML formatting.

**`anypoint-connect`** — identity and environment discovery; application status, deployment
specification, resources, and settings; log retrieval, error analysis, log patterns, and log
statistics; performance, worker, memory, and time-series metrics plus AMQL queries; lifecycle
operations such as restart, scale, deploy, rollback, stop, start, and delete; Exchange search and
publication; API-manager instances, policies, and alerts; Design Center project files; audit log;
Anypoint MQ queues and dead-letter inspection; and Object Store keys and values.

Lifecycle and mutating operations are never part of establishing readiness, and the skills require
explicit authorization before any of them.

## Configuration per host

| Host | File | Shipped form |
| --- | --- | --- |
| Claude Code | bundled in the plugin | `.mcp.json` in the plugin |
| Codex | `.codex/config.toml` | [`install/hosts/codex/config.toml`](https://github.com/Avinava/mule-skills/blob/main/install/hosts/codex/config.toml) |
| VS Code and Copilot in VS Code | `.vscode/mcp.json` | [`install/hosts/vscode/mcp.json`](https://github.com/Avinava/mule-skills/blob/main/install/hosts/vscode/mcp.json) |
| Copilot CLI, Gemini, other hosts accepting `mcpServers` | `.mcp.json` | [`install/hosts/mcp.json`](https://github.com/Avinava/mule-skills/blob/main/install/hosts/mcp.json) |

The generic form:

```json
{
  "mcpServers": {
    "anypoint-connect": {
      "command": "npx",
      "args": ["-y", "@sfdxy/anypoint-connect@0.11.1", "mcp"]
    },
    "mule-build": {
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-build@2.2.0", "mcp"]
    },
    "mule-lint": {
      "command": "npx",
      "args": ["-y", "@sfdxy/mule-lint@1.27.0", "mcp"]
    }
  }
}
```

The installer merges only the entries your configuration lacks and never overwrites an existing
server of the same name. See [Install for other agents](install-other-agents.md).

Local MCP files do not configure GitHub-hosted Copilot agents or code review; configure hosted MCP
access through repository settings. Claude Code asks for approval before using project-scoped MCP
servers.

## Verify and disable

| Host | Verify | Disable one server |
| --- | --- | --- |
| Claude Code | `/mcp` | `/mcp`, then disable it |
| Codex | `codex mcp list` | Remove its `[mcp_servers.<name>]` table |
| Copilot CLI | `copilot mcp list` | Remove its entry from `.mcp.json` |
| VS Code | Reload the window and inspect the MCP server list | Remove its entry from `.vscode/mcp.json` |
| Gemini and others | The host's MCP status view | Remove its entry from the host's config |

The first session after installing pays one `npx` cold start per server while the packages download.
Later sessions use the cache.

## Keeping the pins consistent

The pinned versions appear in the plugin `.mcp.json`, the three host forms, the installer, and this
documentation. `tools/validate_repository.py` fails the build when any of them disagree, so a
version bump has to be applied everywhere or not at all.
