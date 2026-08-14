# Install for Claude Code

Claude Code installs Mule Skills as a plugin. Nothing is copied into your project.

## Install

```text
/plugin marketplace add Avinava/mule-skills
/plugin install mule-skills@mule-skills
```

The first command registers this repository as a plugin marketplace. The second installs the plugin
from it. Both are one-time.

Install for a whole team by committing the scope to the project instead:

```bash
claude plugin marketplace add Avinava/mule-skills
claude plugin install mule-skills@mule-skills --scope project
```

That writes to `.claude/settings.json`, so everyone who clones the repository gets the same plugin.

## What you get

Six skills, namespaced under the plugin:

| Skill | Use it for |
| --- | --- |
| `mule-docs` | Documentation, architecture, APIs, flows, onboarding, targeted refreshes |
| `mule-development` | Mule XML, DataWeave, connectors, error handling, queues, batch, MUnit |
| `mule-troubleshooting` | Incidents, timeouts, connection failures, concurrency, memory |
| `mule-ops` | Runtime health, deployments, logs, metrics, recurring checks |
| `mule-review` | Working changes, commits, branches, PRs, release readiness |
| `mule-build` | Validation, tests, packaging, explicitly requested release actions |

Claude selects them from their descriptions, so you can just describe the task. Plugin skills are
namespaced, so they appear as `mule-skills:mule-review`, `mule-skills:mule-docs`, and so on — use
that form to invoke one directly.

Plus three MCP servers — see below.

## MCP servers

The plugin bundles credential-free launch configuration for three pinned servers:

| Server | Pin | Role |
| --- | --- | --- |
| [`mule-build`](https://github.com/Avinava/mule-build) | `@sfdxy/mule-build@2.0.0` | Validation, testing, packaging, local runtime, security checks |
| [`mule-lint`](https://github.com/Avinava/mule-lint) | `@sfdxy/mule-lint@1.24.1` | Static Mule analysis and machine-readable reports |
| [`anypoint-connect`](https://github.com/Avinava/anypoint-connect) | `@sfdxy/anypoint-connect@0.10.0` | Authorized Anypoint logs, metrics, deployments, Exchange, MQ, Object Store |

Plugin MCP servers start automatically when the plugin is enabled, so the first session after
installing pays three `npx` cold starts. They are cached afterwards. Node.js `>=20.19.0` satisfies
all three.

`mule-build` and `mule-lint` need no credentials. `anypoint-connect` idles until you authenticate —
see [project-setup.md](project-setup.md#optional-anypoint-access).

The `mule-build` skill and the `mule-build` MCP server share a name but are different things: the
skill is the workflow (`mule-skills:mule-build`), the server provides the tools it calls
(`mcp__mule-build__*`). Either can be used without the other.

Run `/mcp` to see connection status or to disable a server you do not want.

## Verify

```text
/plugin
```

`mule-skills` should be listed and enabled. Then ask Claude to do something Mule-shaped and confirm
it picks up the matching skill.

## Update and remove

```text
/plugin marketplace update mule-skills
/plugin update mule-skills@mule-skills
/plugin uninstall mule-skills@mule-skills
```

## Do I still need CLAUDE.md?

Not for routing — Claude discovers plugin skills automatically. You do still want an `AGENTS.md`
holding this project's evidence-backed context, which is what the skills read from. See
[project-setup.md](project-setup.md).
