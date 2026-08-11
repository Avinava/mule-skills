<p align="center">
  <img src="assets/banner.svg" alt="Mule Skills — evidence-backed Mule 4 agent workflows" width="960" />
</p>

<p align="center">
  <strong>Reusable AI-agent skills for MuleSoft Mule 4 documentation, development, troubleshooting, and operations.</strong>
</p>

These skills are designed to be used with AI coding agents (Codex, Claude, Gemini, Cursor, etc.) and work alongside MCP servers like **anypoint-connect**, **mule-build**, and **mule-lint** for full lifecycle coverage.

---

## Quick Setup

Paste this instruction into your AI coding agent (Codex, Claude, Gemini, etc.) when working on a Mule 4 project:

```
Follow the setup instructions at https://github.com/Avinava/mule-skills/blob/main/SETUP.md
to configure this MuleSoft project with AI agent skills.
```

The agent will:

1. Clone this repo
2. Copy universal skills into your project's `.agents/skills/` directory
3. Copy workflow templates into `.agents/workflows/`
4. Configure pinned MCP servers for the agent or IDE you actually use
5. Generate evidence-backed `AGENTS.md` plus optional host-specific context files
6. Validate the installation and commit it when authorized

---

## Skill Index

### Universal Skills (ready to use as-is)

| Skill                         | Path                                | Description                                                                                                                                                                                                                                                                                                                           |
| ----------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document MuleSoft Project** | `skills/document-mulesoft-project/` | Analyzes Mule 4 source and creates or refreshes evidence-backed Markdown documentation. Selects an adaptive document set, explains APIs, flows, integrations, DataWeave, configuration, deployment, testing, and operations, and adds Mermaid diagrams where useful. Includes read-only inventory and privacy/evidence audit scripts. |
| **Mule Development**          | `skills/mule-development/`          | Evidence-based Mule 4 implementation guidance for DataWeave, error handling, serialization, flow design, concurrency, queues, timeouts, state, logging, testing, and documentation. Includes a post-development checklist.                                                                                                                |
| **Mule Troubleshooting**      | `skills/mule-troubleshooting/`      | Structured RCA methodology that traces timeouts, connection failures, rate limits, concurrency, batch, queues, deployment transitions, and memory pressure across the complete execution path.                                                                                                                                        |
| **Mule Ops**                  | `skills/mule-ops/`                  | Role-based runtime health analysis using logs, metrics, deployments, coverage ledgers, cross-application correlation, confidence states, and privacy-safe reporting. Supports one application or any discovered multi-application topology.                                                                                            |
| **Review MuleSoft Project**   | `skills/review-mulesoft-project/`   | Evidence-backed change, PR, whole-project, and release-readiness review. Covers contracts, Mule behavior, delivery semantics, security, tests, operations, and documentation, with prioritized findings and remediation options.                                                                                                        |

### Generic Workflows

| Workflow  | Path                 | Description                                                                                                                   |
| --------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Build** | `workflows/build.md` | Validate and package a Mule application; performs versioning, changelog, commit, tag, publish, or deploy actions only when explicitly requested. |

### Templates (customize per project)

| Template      | Path                  | Description                                                                |
| ------------- | --------------------- | -------------------------------------------------------------------------- |
| **AGENTS.md** | `templates/AGENTS.md` | Project guide for AI agents — architecture, flows, configuration, patterns |
| **GEMINI.md** | `templates/GEMINI.md` | Gemini-specific directives                                                 |
| **CLAUDE.md** | `templates/CLAUDE.md` | Claude-specific directives                                                 |

---

## Repository Structure

```
mule-skills/
├── assets/
│   └── banner.svg                         # README illustration and project banner
├── README.md                              # This file
├── SETUP.md                               # Bootstrap instruction for AI agents
├── skills/
│   ├── mule-development/
│   │   ├── SKILL.md                       # Best practices & patterns (universal)
│   │   ├── agents/openai.yaml             # Codex UI metadata
│   │   └── resources/
│   │       └── post-development-checklist.md  # Gotcha checklist (referenced by skill)
│   ├── document-mulesoft-project/
│   │   ├── SKILL.md                       # Evidence-backed documentation workflow
│   │   ├── agents/openai.yaml             # Codex UI metadata
│   │   ├── references/                    # Analysis, blueprint, Mermaid, and privacy guidance
│   │   └── scripts/                       # Read-only inventory and documentation audit
│   ├── mule-troubleshooting/
│   │   ├── SKILL.md                       # RCA methodology (universal)
│   │   └── agents/openai.yaml             # Codex UI metadata
│   ├── mule-ops/
│   │   ├── SKILL.md                       # Runtime health analysis (universal)
│   │   └── agents/openai.yaml             # Codex UI metadata
│   └── review-mulesoft-project/
│       ├── SKILL.md                       # Change, project, and readiness review
│       ├── agents/openai.yaml             # Codex UI metadata
│       └── references/                    # Review domains and finding policy
├── workflows/
│   └── build.md                           # Generic Mule build workflow
├── mcp/
│   ├── .codex/
│   │   └── config.toml                   # Codex project-scoped MCP config
│   ├── .vscode/
│   │   └── mcp.json                       # VS Code / GitHub Copilot config
│   └── mcp.json                           # Shared mcpServers payload for JSON-based clients
└── templates/
    ├── AGENTS.md                          # Project-specific agent guide
    ├── GEMINI.md                          # Gemini directives template
    └── CLAUDE.md                          # Claude directives template
```

---

## MCP Server Compatibility

These skills are designed to work with:

| MCP Server           | npm Package                     | Purpose                                                                                         | Used By                            |
| -------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------- |
| **anypoint-connect** | `@sfdxy/anypoint-connect@0.9.0` | Anypoint Platform operations — logs, metrics, deployments, API management, Exchange             | `mule-ops`, `mule-troubleshooting`, optional review verification |
| **mule-build**       | `@sfdxy/mule-build@2.0.0`       | Local build, run, release, validation, and security checks                                      | `workflows/build.md`, review validation                           |
| **mule-lint**        | `@sfdxy/mule-lint@1.24.1`       | Static analysis — 82 rules for error handling, security, naming, logging, performance, and more | Post-development checklist, project review                        |

The MCP package versions are pinned for reproducibility. Pre-built configs are provided for Codex,
VS Code, and JSON-based MCP clients. See [SETUP.md](SETUP.md#4-configure-mcp-servers-for-the-active-agent)
for current, host-specific instructions.

Skills will reference MCP tool names (e.g., `mcp_anypoint-connect_get_logs`) but work independently if MCP servers are not available — the methodology is still valid for manual execution.

---

## How Skills Work

Skills are folders of instructions that extend AI agent capabilities. Each skill contains:

- **`SKILL.md`** (required): Main instruction file with YAML frontmatter (`name`, `description`) and detailed markdown instructions
- **`agents/`** (optional): Agent-specific discovery and interface metadata
- **`references/` or `resources/`** (optional): Guidance, checklists, reference data, or examples loaded only when needed
- **`scripts/`** (optional): Deterministic helpers for repeatable analysis and validation

When an AI agent encounters a task matching a skill's description, it reads the `SKILL.md` and follows
the instructions. This repository installs shared project skills in `.agents/skills/`, the
repository-scoped location discovered by Codex. Existing tool-specific agent directories can coexist.

### Directory Placement

```
your-mule-project/
├── .agents/
│   ├── skills/
│   │   ├── document-mulesoft-project/
│   │   │   ├── SKILL.md
│   │   │   ├── agents/openai.yaml
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   ├── mule-development/
│   │   │   ├── SKILL.md
│   │   │   ├── agents/openai.yaml
│   │   │   └── resources/
│   │   │       └── post-development-checklist.md
│   │   ├── mule-troubleshooting/
│   │   │   ├── SKILL.md
│   │   │   └── agents/openai.yaml
│   │   ├── mule-ops/
│   │   │   ├── SKILL.md
│   │   │   └── agents/openai.yaml
│   │   └── review-mulesoft-project/
│   │       ├── SKILL.md
│   │       ├── agents/openai.yaml
│   │       └── references/
│   └── workflows/
│       └── build.md
├── .vscode/
│   └── mcp.json                 # MCP server config (VS Code)
├── .codex/
│   └── config.toml              # MCP server config (Codex)
├── AGENTS.md                    # Project-specific (from template)
├── GEMINI.md                    # Optional
├── CLAUDE.md                    # Optional
├── .anypoint-connect.json       # Anypoint profile binding
├── pom.xml
└── src/
```

---

## Contributing

To add a new skill:

1. Create a folder under `skills/` with a descriptive kebab-case name
2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-new-skill
   description: One-line description of when to use this skill.
   ---
   ```
3. Ensure **zero client-specific references** — no project names, org names, or version numbers
4. Use `<PLACEHOLDER>` syntax for anything that varies per project
5. Validate the skill and run every bundled script against representative inputs
6. Update `README.md` and `SETUP.md` so installation and discovery remain complete
7. Open a PR

---

## License

Private repository — internal use only.
