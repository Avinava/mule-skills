# mule-skills

Reusable AI-agent skills for **MuleSoft Mule 4** development — best practices, troubleshooting, and operational runbooks.

These skills are designed to be used with AI coding agents (Claude, Gemini, Cursor, etc.) and work alongside MCP servers like **anypoint-connect** and **mule-build** for full lifecycle coverage.

---

## Quick Setup

Paste this instruction into your AI coding agent (Claude, Gemini, etc.) when working on a Mule 4 project:

```
Follow the setup instructions at https://github.com/Avinava/mule-skills/blob/main/SETUP.md
to configure this MuleSoft project with AI agent skills.
```

The agent will:
1. Clone this repo
2. Copy universal skills into your project's `.agents/skills/` directory
3. Copy workflow templates into `.agents/workflows/`
4. Generate project-specific `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md` from templates
5. Commit the setup

---

## Skill Index

### Universal Skills (ready to use as-is)

| Skill | Path | Description |
|-------|------|-------------|
| **Mule Development** | `skills/mule-development/` | DataWeave patterns, flow design, error handling, naming conventions, concurrency, SOQL safety, ObjectStore patterns, and common pitfalls. Includes `resources/post-development-checklist.md`. Use every time you modify or create a flow. |
| **Mule Troubleshooting** | `skills/mule-troubleshooting/` | Structured RCA methodology for timeout, concurrency, and connection issues in multi-tier Mule architectures (PAPI → SAPI → External Systems). |
| **Mule Ops** | `skills/mule-ops/` | Production log analysis workflow using Anypoint Monitoring. Covers logs, errors, metrics, memory, performance, and deployment activity. Uses configurable app name placeholders. |

### Generic Workflows

| Workflow | Path | Description |
|----------|------|-------------|
| **Build** | `workflows/build.md` | Build a Mule application JAR — version bump decisions, CHANGELOG maintenance, git tagging, documentation sync, and packaging. |

### Templates (customize per project)

| Template | Path | Description |
|----------|------|-------------|
| **AGENTS.md** | `templates/AGENTS.md` | Project guide for AI agents — architecture, flows, configuration, patterns |
| **GEMINI.md** | `templates/GEMINI.md` | Gemini-specific directives |
| **CLAUDE.md** | `templates/CLAUDE.md` | Claude-specific directives |


---

## Repository Structure

```
mule-skills/
├── README.md                              # This file
├── SETUP.md                               # Bootstrap instruction for AI agents
├── skills/
│   ├── mule-development/
│   │   ├── SKILL.md                       # Best practices & patterns (universal)
│   │   └── resources/
│   │       └── post-development-checklist.md  # Gotcha checklist (referenced by skill)
│   ├── mule-troubleshooting/
│   │   └── SKILL.md                       # RCA methodology (universal)
│   └── mule-ops/
│       └── SKILL.md                       # Production log analysis (configurable)
├── workflows/
│   └── build.md                           # Generic Mule build workflow
└── templates/
    ├── AGENTS.md                          # Project-specific agent guide
    ├── GEMINI.md                          # Gemini directives template
    └── CLAUDE.md                          # Claude directives template
```

---

## MCP Server Compatibility

These skills are designed to work with:

| MCP Server | Purpose | Used By |
|------------|---------|---------|
| **anypoint-connect** | Anypoint Platform operations — logs, metrics, deployments, API management, Exchange | `mule-ops`, `mule-troubleshooting` |
| **mule-build** | Local build, run, and release — Maven packaging, version bumps, security scanning | `workflows/build.md` |

Skills will reference MCP tool names (e.g., `mcp_anypoint-connect_get_logs`) but work independently if MCP servers are not available — the methodology is still valid for manual execution.

---

## How Skills Work

Skills are folders of instructions that extend AI agent capabilities. Each skill contains:

- **`SKILL.md`** (required): Main instruction file with YAML frontmatter (`name`, `description`) and detailed markdown instructions
- **`resources/`** (optional): Additional files like checklists, reference data, or examples

When an AI agent encounters a task matching a skill's description, it reads the `SKILL.md` and follows the instructions. The agent directories can be named `.agents/` or `.agent/` depending on your tooling.

### Directory Placement

```
your-mule-project/
├── .agents/
│   ├── skills/
│   │   ├── mule-development/
│   │   │   └── SKILL.md
│   │   ├── mule-troubleshooting/
│   │   │   └── SKILL.md
│   │   └── mule-ops/
│   │       └── SKILL.md
│   └── workflows/
│       └── build.md
├── AGENTS.md                    # Project-specific (from template)
├── GEMINI.md                    # Optional
├── CLAUDE.md                    # Optional
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
5. Open a PR

---

## License

Private repository — internal use only.
