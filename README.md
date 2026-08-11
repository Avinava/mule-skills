<p align="center">
  <img src="assets/banner.svg" alt="Mule Skills — evidence-backed MuleSoft agent workflows" width="960" />
</p>

<p align="center">
  <strong>Reusable AI-agent workflows for the Mule 4 engineering lifecycle.</strong>
</p>

Mule Skills gives coding agents a shared way to document, build, troubleshoot, operate, and review
MuleSoft projects. The workflows start from current-project evidence, keep business context separate
from implemented behavior, and avoid carrying identity or tuning assumptions between projects.

The skills work as instruction-only workflows and can use the included MCP configurations when
local build, lint, or authorized Anypoint evidence is available.

## Quick start

From the Mule project you want to configure, give your coding agent this instruction:

```text
Follow https://github.com/Avinava/mule-skills/blob/main/SETUP.md to install or reconcile the
MuleSoft skills for this repository. Preserve existing changes, configure only the agent host I use,
and show me the validation results before committing.
```

The setup runbook installs the skills under `.agents/skills/`, adds the build workflow, configures
only the selected MCP host, creates evidence-backed project guidance, and validates the result.

## Included workflows

| Workflow | Use it for | Default result |
| --- | --- | --- |
| [`document-mulesoft-project`](skills/document-mulesoft-project/) | Project documentation, architecture, APIs, flows, onboarding, operations, and targeted refreshes | Evidence-backed Markdown and Mermaid, plus clearly labeled gaps |
| [`mule-development`](skills/mule-development/) | Mule XML, DataWeave, connectors, error handling, queues, batch, configuration, and MUnit changes | Implemented source change with proportionate validation |
| [`mule-troubleshooting`](skills/mule-troubleshooting/) | Incidents, timeouts, connection failures, rate limits, concurrency, memory, and cross-application failures | Root-cause assessment or fix plan; no source change unless requested |
| [`mule-ops`](skills/mule-ops/) | Runtime health, deployments, logs, metrics, recurring checks, and multi-application correlation | Evidence-backed operational assessment |
| [`review-mulesoft-project`](skills/review-mulesoft-project/) | Working changes, commits, branches, PRs, whole projects, and release readiness | Prioritized findings and fix options; no implementation or PR-state change unless requested |
| [`build`](workflows/build.md) | Validation, tests, packaging, and explicitly requested release actions | Deployable artifact and validation summary |

### Choosing the right workflow

| Request | Start with | Add when needed |
| --- | --- | --- |
| Explain or refresh the project | Documentation | Optional business-context questions when source cannot establish purpose or ownership |
| Implement a change | Development | Documentation refresh, then change review |
| Diagnose a symptom | Troubleshooting | Ops for authorized runtime evidence; development only when a fix is requested |
| Assess current runtime health | Ops | Troubleshooting when a specific causal question emerges |
| Review a change or repository | Project review | Ops only for authorized, material runtime verification |
| Prepare a release | Build | Release-readiness review before commit, tag, publish, or deploy |

Documentation and review questions are optional and non-blocking. When business information would
materially improve the result, the skill offers concise choices plus `Other` and `Not sure / Skip`,
then continues with verified technical evidence if the user skips.

## Operating principles

- **Evidence before assumption:** distinguish verified source or telemetry, user-provided context,
  inference, recommendations, and unresolved gaps.
- **Current project only:** never transplant application identity, topology, endpoints, payloads,
  schedules, volumes, incident fingerprints, or numeric tuning from another project.
- **Privacy by default:** never expose credentials, secret values, private keys, tenant identifiers,
  private hosts, personal data, or raw production payloads.
- **Proportionate validation:** use focused checks for local changes and the complete required gate
  for release readiness.
- **Explicit mutations:** reviews and diagnosis are read-only by default; commits, comments, tags,
  deployments, and releases require user authorization.
- **Honest uncertainty:** missing access or evidence remains visible instead of being converted into
  a confident claim.

## MCP support

The repository includes credential-free launch configurations for three pinned MCP servers:

| Server | Pinned package | Role |
| --- | --- | --- |
| `anypoint-connect` | `@sfdxy/anypoint-connect@0.9.0` | Authorized Anypoint logs, metrics, deployments, API management, Exchange, MQ, and Object Store evidence |
| `mule-build` | `@sfdxy/mule-build@2.0.0` | Mule validation, testing, packaging, local runtime, versioning, and security checks |
| `mule-lint` | `@sfdxy/mule-lint@1.24.1` | Static Mule analysis and machine-readable reports |

Templates are provided for Codex (`mcp/.codex/config.toml`), VS Code and GitHub Copilot
(`mcp/.vscode/mcp.json`), and hosts such as Claude Code or Copilot CLI that accept a project
`mcpServers` object (`mcp/mcp.json`). Configure only the host in use and merge with existing settings
rather than replacing them. The detailed procedure is in
[SETUP.md](SETUP.md#4-configure-the-selected-mcp-host).

Codex discovers repository-scoped skills from `.agents/skills/` between the working directory and
the repository root. See the official [Codex skills documentation](https://developers.openai.com/codex/skills/)
and [Codex MCP documentation](https://developers.openai.com/codex/mcp/) for current host behavior.

## Repository layout

```text
mule-skills/
├── assets/                         # Project artwork
├── skills/
│   ├── document-mulesoft-project/  # Documentation workflow, references, and audit tools
│   ├── mule-development/           # Implementation workflow and post-change checklist
│   ├── mule-troubleshooting/       # Root-cause analysis workflow
│   ├── mule-ops/                   # Runtime health workflow
│   └── review-mulesoft-project/    # Change, project, and release-readiness review
├── workflows/build.md              # Validate, package, and explicit release workflow
├── templates/                      # Project-owned AGENTS, Claude, Copilot, and Gemini guidance
├── mcp/                            # Codex, VS Code, and generic JSON MCP templates
├── README.md                       # Toolkit overview
└── SETUP.md                        # Installation and reconciliation runbook
```

Each skill has a required `SKILL.md` and may include:

- `agents/openai.yaml` for interface metadata;
- `references/` or `resources/` for guidance loaded by the workflow;
- `scripts/` for deterministic, repeatable inspection and validation.

Host instruction templates keep shared project facts in `AGENTS.md` and add only host-specific
routing:

| Template | Installed path | Host |
| --- | --- | --- |
| `templates/AGENTS.md` | `AGENTS.md` | Shared project context for coding agents |
| `templates/CLAUDE.md` | `CLAUDE.md` | Claude Code |
| `templates/copilot-instructions.md` | `.github/copilot-instructions.md` | GitHub Copilot Chat, coding agent, CLI, and code review where supported |
| `templates/GEMINI.md` | `GEMINI.md` | Gemini coding agents |

After installation, the shared project layout is:

```text
your-mule-project/
├── .agents/
│   ├── skills/                     # The five reusable Mule skills
│   └── workflows/build.md
├── .codex/config.toml              # Optional Codex MCP configuration
├── .vscode/mcp.json                # Optional VS Code MCP configuration
├── .mcp.json                       # Optional Claude Code or Copilot CLI MCP configuration
├── .github/copilot-instructions.md # Optional GitHub Copilot repository instructions
├── AGENTS.md                       # Evidence-backed project context
├── CLAUDE.md                       # Optional Claude Code guidance
├── GEMINI.md                       # Optional host-specific guidance
├── pom.xml
└── src/
```

## Example prompts

```text
Use $document-mulesoft-project to refresh architecture and operations documentation. Ask optional
business questions with choices where the repository cannot establish important context.

Use $mule-development to implement this Mule change and complete the post-development checklist.

Use $mule-troubleshooting to diagnose this timeout. Separate observations, hypotheses, confirmed
causes, and unresolved gaps.

Use $mule-ops to assess runtime health for the requested environment and time window.

Use $review-mulesoft-project in change-review mode for this branch. Report findings and fix options;
do not modify source or post PR comments.

Use the build workflow to package the application. Do not release, tag, deploy, or push.
```

## Contributing

When adding or changing a reusable skill:

1. Keep the workflow focused and give its `SKILL.md` a precise trigger description.
2. Put project-specific identity, topology, and operating facts in the consuming repository, never
   in this reusable repository.
3. Use neutral examples and mechanism-based guidance; do not retain prior-project fingerprints or
   numeric tuning values.
4. Add `agents/openai.yaml` and only the references, resources, scripts, or assets the skill needs.
5. Validate the skill, test it with neutral representative tasks, and inspect outputs for unsupported
   claims or sensitive data.
6. Update README and SETUP when discovery, installation, routing, or required resources change.

## License

Private repository — internal use only.
