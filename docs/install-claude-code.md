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

Eight skills, namespaced under the plugin:

| Skill | Use it for |
| --- | --- |
| `mule-api-design` | HTTP API workshops, RAML/OAS contracts, assessment, Design Center workflow |
| `mule-docs` | Documentation, architecture, APIs, flows, onboarding, targeted refreshes |
| `mule-development` | Mule production XML, DataWeave, APIKit implementation, connectors, queues, batch |
| `mule-testing` | MUnit authoring, repair, fixtures, mocks, assertions, test-only configuration |
| `mule-troubleshooting` | Incidents, timeouts, connection failures, concurrency, memory |
| `mule-ops` | Runtime health, deployments, logs, metrics, recurring checks |
| `mule-review` | Working changes, commits, branches, PRs, release readiness |
| `mule-build` | Local validation, tests, packaging, runtime work, versioning, and tags |

Claude selects them from their descriptions, so you can just describe the task. Plugin skills are
namespaced, so they appear as `mule-skills:mule-review`, `mule-skills:mule-docs`, and so on — use
that form to invoke one directly.

Plus three MCP servers — see below.

## MCP servers

The plugin bundles credential-free launch configuration for three pinned servers:

| Server | Pin | Role |
| --- | --- | --- |
| [`mule-build`](https://github.com/Avinava/mule-build) | `@sfdxy/mule-build@2.3.0` | Validation, testing, packaging, local runtime, versioning, tagging, security checks |
| [`mule-lint`](https://github.com/Avinava/mule-lint) | `@sfdxy/mule-lint@1.30.1` | Canonical Mule standards, static analysis, XML formatting, RAML/OAS validation |
| [`anypoint-connect`](https://github.com/Avinava/anypoint-connect) | `@sfdxy/anypoint-connect@0.13.0` | Authorized Design Center, Exchange, Governance, runtime evidence, mutations |

Plugin MCP servers start automatically when the plugin is enabled, so the first session after
installing pays three `npx` cold starts. They are cached afterwards.
Node.js `>=22.0.0` satisfies all three; Node.js 24 LTS is recommended.

`mule-build` and `mule-lint` need no credentials. `anypoint-connect` idles until you authenticate —
see [anypoint-access.md](anypoint-access.md). Skills that need Anypoint evidence probe the requested capability
first and offer setup, supplied exports, or a repository-only scope, so an unauthenticated connector
never blocks a session.

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
