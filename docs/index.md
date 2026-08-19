# Mule Skills

<img src="assets/banner.svg" alt="Mule Skills — evidence-backed MuleSoft agent workflows" width="960" />

Mule Skills gives coding agents a shared way to document, build, troubleshoot, operate, and review
MuleSoft Mule 4 projects. The workflows start from current-project evidence, keep business context
separate from implemented behavior, and avoid carrying identity or tuning assumptions between
projects.

The skills work as instruction-only workflows. They can also use three pinned MCP servers when
local build, lint, or authorized Anypoint evidence is available.

## Start here

| You are | Go to |
| --- | --- |
| A Claude Code user | [Install for Claude Code](install-claude-code.md) |
| A Codex, Copilot, or Gemini user | [Install for other agents](install-other-agents.md) |
| Using a host with no plugin support and no shell | [Agent-driven install](agent-install.md) |
| Installed, and giving the skills project context | [Project setup](project-setup.md) |
| Wanting runtime logs, metrics, or deployment evidence | [Anypoint access](anypoint-access.md) |
| Choosing packages or checking supported versions | [Ecosystem](ecosystem.md) |

Installing places files. [Project setup](project-setup.md) is the part that needs judgment, and it
matters for every install path.

## The six skills

| Skill | Use it for | Default result |
| --- | --- | --- |
| `mule-docs` | Documentation, architecture, APIs, flows, onboarding, operations | Evidence-backed Markdown and Mermaid, plus labeled gaps |
| `mule-development` | Mule XML, DataWeave, connectors, error handling, queues, batch, MUnit | Implemented change with proportionate validation |
| `mule-troubleshooting` | Incidents, timeouts, connection failures, concurrency, memory | Root-cause assessment or fix plan, no source change unless asked |
| `mule-ops` | Runtime health, deployments, logs, metrics, recurring checks | Evidence-backed operational assessment |
| `mule-review` | Working changes, commits, branches, PRs, release readiness | Prioritized findings and fix options |
| `mule-build` | Validation, tests, packaging, explicitly requested release actions | Deployable artifact and validation summary |

Details and routing guidance are on the [Skills](skills.md) page.

## The three MCP servers

| Server | Pin | Credentials | Its own docs |
| --- | --- | --- | --- |
| `mule-build` | `@sfdxy/mule-build@2.2.0` | None | <https://avinava.github.io/mule-build/> |
| `mule-lint` | `@sfdxy/mule-lint@1.26.0` | None | <https://avinava.github.io/mule-lint/> |
| `anypoint-connect` | `@sfdxy/anypoint-connect@0.11.1` | Anypoint Platform login | <https://avinava.github.io/anypoint-connect/> |

`anypoint-connect` idles until you authenticate. Skills that need runtime evidence probe for access
first and offer you a choice — set it up, supply exported logs and metrics, or continue with
repository-only analysis and labeled gaps. See [Anypoint access](anypoint-access.md) and
[MCP servers](mcp-servers.md).

## Requirements

- Node.js `>=20.19.0` for the MCP servers
- Python 3 for the bundled inventory, audit, and check scripts
- A Mule 4 repository to work in

## Operating principles

- **Evidence before assumption:** separate verified source or telemetry, user-provided context,
  inference, recommendations, and unresolved gaps.
- **Current project only:** never transplant identity, topology, endpoints, payloads, schedules,
  volumes, incident fingerprints, or numeric tuning from another project.
- **Privacy by default:** never expose credentials, secret values, tenant identifiers, private
  hosts, personal data, or raw production payloads.
- **Proportionate validation:** focused checks for local changes, the full gate for release
  readiness.
- **Explicit mutations:** review and diagnosis are read-only; commits, comments, tags, deployments,
  and releases need authorization.
- **Honest uncertainty:** missing access or evidence stays visible instead of becoming a confident
  claim.
