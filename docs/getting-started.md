# Getting started in one Mule project

You do not need to learn how skills or MCP work internally. Start from a Mule 4 repository and tell
the agent what you want in MuleSoft terms.

## Before installation

Keep the project open at the directory containing `pom.xml` and `mule-artifact.json`. Installation
adds agent instructions and, for non-plugin hosts, vendored skills and MCP configuration. It does not
edit Mule XML, DataWeave, RAML, properties, or the POM.

The optional MCP servers need Node.js 22 or newer. Bundled inventory/check scripts need Python 3.
Your normal Maven, JDK, Mule runtime, and Anypoint requirements still apply to the tasks that use
them.

## Choose the easiest path

| Your agent | Recommended install | What changes in the project |
| --- | --- | --- |
| Claude Code | [Plugin install](install-claude-code.md) | Nothing; the plugin owns skills and MCP configuration |
| Codex, Copilot, Gemini, Cursor | [Agent or script install](install-other-agents.md) | `.agents/skills/`, host instructions, selected MCP config |
| Another agent or no shell | [Agent-driven runbook](agent-install.md) | Only the files its host supports, after preview |

If you are unsure, use the copyable instruction on the [home page](index.md#paste-one-instruction).
The runbook detects the host and existing configuration before changing anything.

## What a preview should show

A first install should describe, in plain language:

```text
Install mode: new installation
Skills: 8 to add under .agents/skills
Hosts: detected from existing repository configuration
MCP: add missing mule-build, mule-lint, and anypoint-connect entries
Preserved: existing AGENTS.md and customized host configuration
Next: run repository inventory and configuration validation
```

Exact paths differ by host. If an entry with the same MCP name already exists, the installer leaves
it unchanged and reports it. An upgrade diffs the current bundle and preserves project-owned files.

## Give the agent project context

Installation teaches the workflow; [project setup](project-setup.md) teaches it this application.
The agent should derive what it can from source and ask only for important facts that source cannot
prove, such as intended consumers, business capability, ownership, deployment target, or operational
expectations.

The resulting `AGENTS.md` should describe this project without embedding secrets or environment
values. Review it before asking for implementation work.

## Make the first request

You can name a skill, but usually the task is enough:

```text
Explain this Mule application to a developer joining the team. Separate what the repository proves
from business context you still need.
```

```text
Add MUnit coverage for the order lookup error path. Keep the event faithful to the real caller, mock
only the outbound boundary, and run the focused test before the full required suite.
```

```text
Validate and package this Mule application. Show the checks, MUnit totals, and artifact path. Do not
version, tag, publish, or deploy anything.
```

The [evidence-backed journeys](see-it-in-action.md) show what a developer actually receives. The
[workflow examples](workflows.md) explain the reusable paths and approval boundaries.

## When Anypoint access appears

Local documentation, implementation, static analysis, tests, and packaging do not need Anypoint
credentials. The agent offers [Anypoint access](anypoint-access.md) only when a request genuinely
needs Design Center, Exchange, Governance, logs, metrics, deployment state, or a platform mutation.
Authentication is never part of installation.
