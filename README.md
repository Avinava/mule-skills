<p align="center">
  <img src="docs/assets/banner.svg" alt="Mule Skills — evidence-backed MuleSoft agent workflows" width="960" />
</p>

<p align="center">
  <strong>Reusable AI-agent workflows for the Mule 4 engineering lifecycle.</strong>
</p>

<p align="center">
  <a href="https://avinava.github.io/mule-skills/">Documentation</a> ·
  <a href="https://avinava.github.io/mule-skills/anypoint-access/">Anypoint access</a> ·
  <a href="https://avinava.github.io/mule-skills/faq/">FAQ</a>
</p>

Mule Skills gives coding agents a shared way to document, build, troubleshoot, operate, and review
MuleSoft projects. The workflows start from current-project evidence, keep business context separate
from implemented behavior, and avoid carrying identity or tuning assumptions between projects.

The skills work as instruction-only workflows and can use the included MCP configurations when
local build, lint, or authorized Anypoint evidence is available.

## Install

Pick the path that matches your agent. All three install the same six skills.

### Claude Code — plugin

```text
/plugin marketplace add Avinava/mule-skills
/plugin install mule-skills@mule-skills
```

That's it. Skills and MCP servers come with the plugin; nothing is copied into your project. Details
in [docs/install-claude-code.md](docs/install-claude-code.md).

### Codex, Copilot, Gemini — script

From the root of your Mule project:

```bash
curl -fsSL https://raw.githubusercontent.com/Avinava/mule-skills/main/install/install.sh | bash
```

It detects your hosts, vendors the skills into `.agents/skills/`, and merges MCP configuration
without overwriting what is already there. Add `--dry-run` to preview. Options and host reference in
[docs/install-other-agents.md](docs/install-other-agents.md).

### Any agent — paste this prompt

Works anywhere, including hosts with no plugin support and no shell:

```text
Follow https://github.com/Avinava/mule-skills/blob/main/docs/agent-install.md to install or
reconcile the MuleSoft skills for this repository. Preserve existing changes, configure only the
agent hosts I use, and show me the validation results before committing.
```

Then give the agent context about your project by following
[docs/project-setup.md](docs/project-setup.md) — that step matters for every install path.

## Skills

| Skill | Use it for | Default result |
| --- | --- | --- |
| [`mule-docs`](skills/mule-docs/) | Project documentation, architecture, APIs, flows, onboarding, operations, and targeted refreshes | Evidence-backed Markdown and Mermaid, plus clearly labeled gaps |
| [`mule-development`](skills/mule-development/) | Mule XML, DataWeave, connectors, error handling, queues, batch, configuration, and MUnit changes | Implemented source change with proportionate validation |
| [`mule-troubleshooting`](skills/mule-troubleshooting/) | Incidents, timeouts, connection failures, rate limits, concurrency, memory, and cross-application failures | Root-cause assessment or fix plan; no source change unless requested |
| [`mule-ops`](skills/mule-ops/) | Runtime health, deployments, logs, metrics, recurring checks, and multi-application correlation | Evidence-backed operational assessment |
| [`mule-review`](skills/mule-review/) | Working changes, commits, branches, PRs, whole projects, and release readiness | Prioritized findings and fix options; no implementation or PR-state change unless requested |
| [`mule-build`](skills/mule-build/) | Validation, tests, packaging, and explicitly requested release actions | Deployable artifact and validation summary |

### Choosing the right skill

| Request | Start with | Add when needed |
| --- | --- | --- |
| Explain or refresh the project | `mule-docs` | Optional business-context questions when source cannot establish purpose or ownership |
| Implement a change | `mule-development` | Documentation refresh, then change review |
| Diagnose a symptom | `mule-troubleshooting` | `mule-ops` for authorized runtime evidence; development only when a fix is requested |
| Assess current runtime health | `mule-ops` | `mule-troubleshooting` when a specific causal question emerges |
| Review a change or repository | `mule-review` | `mule-ops` only for authorized, material runtime verification |
| Prepare a release | `mule-build` | Release-readiness review before commit, tag, publish, or deploy |

Documentation and review questions are optional and non-blocking. When business information would
materially improve the result, the skill offers concise choices plus `Other` and `Not sure / Skip`,
then continues with verified technical evidence if the user skips.

## Agent support

The six skills are shared and host-neutral. Claude Code loads them from the plugin; every other host
reads them from `.agents/skills/`, with instruction files telling the agent how to route.

| Host | Skill discovery | Repository instructions | MCP configuration | Verification |
| --- | --- | --- | --- | --- |
| Claude Code | Plugin (`/plugin install`) | `AGENTS.md`; `CLAUDE.md` optional | Bundled in the plugin | `/plugin`, `/mcp` |
| Codex CLI, desktop, and IDE extension | `.agents/skills/` | `AGENTS.md` | `.codex/config.toml` | `codex mcp list` |
| GitHub Copilot in VS Code | `.agents/skills/` | `.github/copilot-instructions.md` and supported `AGENTS.md` surfaces | `.vscode/mcp.json` | Reload VS Code and inspect its MCP server list |
| GitHub Copilot CLI | `.agents/skills/` | `.github/copilot-instructions.md` and `AGENTS.md` | `.mcp.json` | `copilot mcp list` |
| Gemini coding agents | `.agents/skills/` | `GEMINI.md` and `AGENTS.md` | `.mcp.json` where supported | The host's MCP status view |
| Other compatible coding agents | `.agents/skills/` | `AGENTS.md` plus host-supported instruction files | `.mcp.json` when the host accepts `mcpServers` | The host's documented MCP check |

Local MCP files do not configure GitHub-hosted Copilot agents or code review; configure hosted MCP
access through repository settings. Claude Code asks for approval before using project-scoped MCP
servers.

Current host behavior is documented by [OpenAI Docs for Codex skills](https://developers.openai.com/codex/skills/),
[OpenAI Docs for Codex MCP](https://developers.openai.com/codex/mcp/),
[Anthropic's Claude Code guidance](https://docs.anthropic.com/en/docs/claude-code/memory), and
[GitHub Copilot custom-instruction guidance](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide).

## Operating principles

- **Evidence before assumption:** distinguish verified source or telemetry, user-provided context,
  inference, recommendations, and unresolved gaps.
- **Current project only:** never transplant application identity, topology, endpoints, payloads,
  schedules, volumes, incident fingerprints, or numeric tuning from another project.
- **Privacy by default:** never expose credentials, secret values, private keys, tenant identifiers,
  private hosts, personal data, or raw production payloads.
- **Proportionate validation:** use focused checks for local changes and the complete required gate
  for release readiness.
- **Shared mechanism model:** use Classes A–E for value, embedding, contract, failure, and state
  invariants, plus explicit cross-cutting security, capacity, delivery, privacy, and validation gates.
- **Explicit mutations:** reviews and diagnosis are read-only by default; commits, comments, tags,
  deployments, and releases require user authorization.
- **Honest uncertainty:** missing access or evidence remains visible instead of being converted into
  a confident claim.

## MCP support

Credential-free launch configuration for three pinned MCP servers:

| Server and source | Exact package pin | Role |
| --- | --- | --- |
| [`anypoint-connect`](https://github.com/Avinava/anypoint-connect) | [`@sfdxy/anypoint-connect@0.11.1`](https://registry.npmjs.org/@sfdxy%2Fanypoint-connect/0.11.1) | Authorized Anypoint logs, metrics, deployments, API management, Exchange, MQ, and Object Store evidence |
| [`mule-build`](https://github.com/Avinava/mule-build) | [`@sfdxy/mule-build@2.2.0`](https://registry.npmjs.org/@sfdxy%2Fmule-build/2.2.0) | Mule validation, testing, packaging, local runtime, versioning, and security checks |
| [`mule-lint`](https://github.com/Avinava/mule-lint) | [`@sfdxy/mule-lint@1.26.0`](https://registry.npmjs.org/@sfdxy%2Fmule-lint/1.26.0) | Canonical Mule standards, static analysis, rule profiles, and machine-readable guidance |

Source links come from each published package's repository metadata. Package links resolve to the
exact registry version used by the checked-in configuration rather than an unpinned latest release.
Node.js `>=20.19.0` satisfies all three.

`mule-build` and `mule-lint` need no credentials. `anypoint-connect` idles until you authenticate;
see [docs/anypoint-access.md](docs/anypoint-access.md).

Skills that need runtime evidence — `mule-ops`, `mule-troubleshooting`, `mule-review`, and the
publish and deploy actions in `mule-build` — probe for Anypoint access before their first connector
call. When it is missing they say which state they found and offer setup, exported logs and metrics
you supply, or a repository-only scope with the gap labeled. Nothing blocks on authentication, and a
tool error is never reported as an environment finding. The shared workflow is
[`skills/mule-ops/references/anypoint-readiness.md`](skills/mule-ops/references/anypoint-readiness.md).

The plugin ships `.mcp.json` and starts these servers automatically when it is enabled — run `/mcp`
to check status or disable one. For other hosts, `install/hosts/` holds the Codex, VS Code, and
generic JSON forms, and the installer merges only the entries your config lacks.

## Repository layout

```text
mule-skills/
├── .claude-plugin/                 # Plugin and marketplace manifests
├── .mcp.json                       # Pinned MCP servers shipped with the plugin
├── skills/                         # The six reusable skills — host-neutral
│   ├── mule-docs/                  # Documentation workflow, references, and audit tools
│   ├── mule-development/           # Implementation workflow and post-change checklist
│   ├── mule-troubleshooting/       # Root-cause analysis workflow
│   ├── mule-ops/                   # Runtime health workflow
│   ├── mule-review/                # Change, project, and release-readiness review
│   └── mule-build/                 # Validate, package, and explicit release workflow
├── install/
│   ├── install.sh                  # Vendored install for non-plugin hosts
│   ├── hosts/                      # Codex, VS Code, and generic JSON MCP configurations
│   └── templates/                  # Project-owned AGENTS, Claude, Copilot, and Gemini guidance
├── tools/                          # Dependency-free repository validation
├── tests/                          # Validator and checker tests
├── docs/                           # Documentation site source, published with GitHub Pages
├── mkdocs.yml                      # Site configuration and navigation
├── requirements-docs.txt           # Site build dependency, pinned
├── README.md
└── SETUP.md                        # Redirect to docs/
```

Each skill has a required `SKILL.md` and may include:

- `agents/openai.yaml` for interface metadata;
- `references/` or `resources/` for guidance loaded by the workflow;
- `scripts/` for deterministic, repeatable inspection and validation.

Skills refer to bundled scripts through `<skill-root>` and `<skills-root>` placeholders rather than a
fixed path, so the same file works under a plugin install and a vendored install.

## Example prompts

```text
Use mule-docs to refresh architecture and operations documentation. Ask optional business questions
with choices where the repository cannot establish important context.

Use mule-development to implement this Mule change and complete the post-development checklist.

Use mule-troubleshooting to find the root cause of the timeouts in this flow, then stop before
changing anything.

Use mule-review in change-review mode for this branch. Report findings and fix options; do not
modify source or PR state.

Use mule-build to validate and package this application without performing any release action.
```

## Contributing

When adding or changing a reusable skill:

1. Keep the workflow focused and give its `SKILL.md` a precise trigger description.
2. Put project-specific identity, topology, and operating facts in the consuming repository, never
   in this reusable repository.
3. Use neutral examples and mechanism-based guidance; do not retain prior-project fingerprints or
   numeric tuning values.
4. Add `agents/openai.yaml` and only the references, resources, scripts, or assets the skill needs.
5. Refer to bundled scripts through `<skill-root>` or `<skills-root>`, never a host-specific path.
6. Validate the skill, test it with neutral representative tasks, and inspect outputs for unsupported
   claims or sensitive data.
7. Update the README, `docs/`, and `install/install.sh` when discovery, installation, routing, or
   required resources change.

Run before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_repository.py .
python3 skills/mule-docs/scripts/audit_documentation.py .
claude plugin validate . --strict
pip install -r requirements-docs.txt && mkdocs build --strict
```

The validator enforces the invariants that documentation alone cannot: MCP pins agree everywhere,
every page under `docs/` is reachable from the site navigation, and the skills that need authorized
runtime evidence route through the shared readiness reference.

CI runs the same checks. See [CHANGELOG.md](CHANGELOG.md) for release history, including the skill
rename table.

## License

[MIT](LICENSE)
