# MuleSoft Skills — Agent Setup Instructions

> **This file is an instruction set for AI coding agents.** When a user provides this URL,
> follow these steps from the root of the Mule project being configured. Inspect first, preserve
> existing project conventions, and ask only for facts that cannot be derived safely from source.

## Safety and scope

- Treat the target repository as user-owned. Preserve unrelated and uncommitted changes.
- Do not rename or delete an existing `.agent/`, `.agents/`, `.codex/`, `.cursor/`, or `.vscode/`
  directory. Use `.agents/skills/` for the shared skills installed by this repository.
- Never place credentials, access tokens, client secrets, or tenant IDs in agent or MCP configuration.
  Keep reusable skills customer-neutral; include project-specific business names only when necessary
  and confirmed by the user.
- Configure only the agent hosts the user actually uses. Ask before changing files outside the
  project, such as a user-level IDE or desktop configuration.
- Show the final diff before committing. Do not push unless the user explicitly requests it.

## Verified toolchain

These instructions were last verified on **2026-08-11** against:

| Component                 | Verified version |
| ------------------------- | ---------------: |
| `@sfdxy/anypoint-connect` |          `0.9.0` |
| `@sfdxy/mule-build`       |          `2.0.0` |
| `@sfdxy/mule-lint`        |         `1.24.1` |

The MCP templates pin these versions so a future package release cannot silently change a project's
tooling. Upgrade the pins deliberately after reviewing the upstream release notes.

## 1. Verify the project and prerequisites

Confirm all of the following before modifying the project:

1. The current directory is the project root and contains `pom.xml`.
2. `pom.xml` declares `<packaging>mule-application</packaging>` or configures
   `mule-maven-plugin`.
3. `git`, `python3`, `node`, `npm`, and `npx` are available.
4. Node.js satisfies `>=20.19.0`. Prefer a supported LTS release (20.19+, 22, or 24).
5. `git status --short` has been reviewed. Existing changes must remain intact.

If the directory is not a Mule 4 project, stop and explain which check failed. If a runtime
prerequisite is missing, report the exact prerequisite instead of partially installing the setup.

## 2. Clone into an isolated temporary directory

Do not use a fixed path such as `/tmp/mule-skills`; it may already contain user data.

```bash
MULE_SKILLS_TMP="$(mktemp -d "${TMPDIR:-/tmp}/mule-skills.XXXXXX")"
git clone --depth 1 https://github.com/Avinava/mule-skills.git "$MULE_SKILLS_TMP"
```

Keep `MULE_SKILLS_TMP` set until cleanup in Step 12. If cloning fails, leave the project unchanged
and ask the user to confirm repository access.

## 3. Install the shared skills and workflow

Create the canonical repository-scoped skill directories:

```bash
mkdir -p .agents/skills .agents/workflows
```

Copy the five skills and build workflow:

```bash
cp -R "$MULE_SKILLS_TMP/skills/document-mulesoft-project" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-development" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-troubleshooting" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-ops" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/review-mulesoft-project" .agents/skills/
cp "$MULE_SKILLS_TMP/workflows/build.md" .agents/workflows/build.md
```

If any destination already exists, compare it with the source before copying. Preserve intentional
local changes, but keep deployed application names, organization identity, and project topology in
project context rather than modifying the reusable skill files.

Codex discovers repository skills from `.agents/skills/` between the current directory and the Git
root. Other agents can read the same files directly even if they also use a tool-specific directory.

## 4. Configure MCP servers for the active agent

The repository ships three credential-free MCP launch entries:

| Server             | Package                         | Purpose                                                                                                          |
| ------------------ | ------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `anypoint-connect` | `@sfdxy/anypoint-connect@0.9.0` | Anypoint applications, logs, metrics, deployments, API management, Exchange, Design Center, MQ, and Object Store |
| `mule-build`       | `@sfdxy/mule-build@2.0.0`       | Mule build, validation, versioning, local runtime, and security checks                                           |
| `mule-lint`        | `@sfdxy/mule-lint@1.24.1`       | Static analysis with 82 rules and table, JSON, SARIF, HTML, and CSV output                                       |

Determine which agent or IDE the user is using. Configure only that host:

| Agent / IDE                              | Project or user config                                                                 | Action                                                           |
| ---------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Codex CLI, desktop, or IDE extension** | Project `.codex/config.toml`                                                           | Copy `mcp/.codex/config.toml`                                    |
| **VS Code / GitHub Copilot**             | Project `.vscode/mcp.json`                                                             | Copy `mcp/.vscode/mcp.json`                                      |
| **Claude Code**                          | Project `.mcp.json`                                                                    | Copy `mcp/mcp.json`                                              |
| **Cursor**                               | Project `.cursor/mcp.json`                                                             | Copy `mcp/mcp.json`                                              |
| **Gemini Code Assist for VS Code**       | User `~/.gemini/settings.json`                                                         | Merge the `mcpServers` object from `mcp/mcp.json` after approval |
| **Claude Desktop**                       | User config (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`) | Merge the `mcpServers` object from `mcp/mcp.json` after approval |
| **Windsurf Cascade**                     | User `~/.codeium/windsurf/mcp_config.json`                                             | Merge the `mcpServers` object from `mcp/mcp.json` after approval |

### Codex

```bash
mkdir -p .codex
cp "$MULE_SKILLS_TMP/mcp/.codex/config.toml" .codex/config.toml
codex mcp list
```

Codex also supports `codex mcp add`, but the checked-in project configuration is reproducible and is
shared by Codex CLI, desktop, and the IDE extension. Codex requires the project to be trusted before
loading project-scoped MCP configuration. See the official [Codex MCP documentation](https://developers.openai.com/codex/mcp/).

### VS Code / GitHub Copilot

```bash
mkdir -p .vscode
cp "$MULE_SKILLS_TMP/mcp/.vscode/mcp.json" .vscode/mcp.json
```

Merge the `servers` object instead of replacing `.vscode/mcp.json` when that file already exists.

### Claude Code or Cursor

```bash
# Claude Code
cp "$MULE_SKILLS_TMP/mcp/mcp.json" .mcp.json

# Cursor (use this instead of the Claude Code destination)
mkdir -p .cursor
cp "$MULE_SKILLS_TMP/mcp/mcp.json" .cursor/mcp.json
```

Merge the `mcpServers` object when the destination already exists. Do not create a root `mcp.json`;
neither Claude Code nor Cursor uses that path for shared project configuration.

### User-level clients

For Gemini Code Assist, Claude Desktop, or Windsurf, display the relevant destination and proposed
`mcpServers` block, then obtain approval before editing the user-level file. Preserve all existing
servers and settings. Never copy secrets into a project or user configuration.

After configuration, restart or reload the active client and verify all three servers initialize.

## 5. Configure Anypoint authentication when needed

Only `anypoint-connect` requires Anypoint authentication. If the project will use Anypoint operations,
ask whether the user has already configured and authenticated a profile.

For a new setup, first check whether `anc` is already available. Obtain approval before installing a
global npm package:

```bash
npm install -g @sfdxy/anypoint-connect@0.9.0
anc config init
anc auth login
anc auth status
```

For multiple Anypoint organizations, use a neutral local profile identifier and bind it to the current
project:

```bash
anc config init --profile org-a
anc auth login --profile org-a
anc config use org-a
anc auth status
```

`anc config use` creates `.anypoint-connect.json`. It contains a local profile binding, not credentials,
but it can reveal an organization label and is machine-specific. Keep it out of version control and do
not use customer names as profile identifiers.

## 6. Verify the installed skill resources

```bash
test -f .agents/skills/document-mulesoft-project/SKILL.md
test -f .agents/skills/document-mulesoft-project/agents/openai.yaml
test -f .agents/skills/document-mulesoft-project/references/privacy-and-evidence.md
test -f .agents/skills/document-mulesoft-project/scripts/audit_documentation.py
test -f .agents/skills/mule-development/agents/openai.yaml
test -f .agents/skills/mule-development/resources/post-development-checklist.md
test -f .agents/skills/mule-troubleshooting/agents/openai.yaml
test -f .agents/skills/mule-ops/agents/openai.yaml
test -f .agents/skills/review-mulesoft-project/SKILL.md
test -f .agents/skills/review-mulesoft-project/agents/openai.yaml
test -f .agents/skills/review-mulesoft-project/references/finding-policy.md
test -f .agents/skills/review-mulesoft-project/references/review-domains.md
test -f .agents/workflows/build.md
python3 .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py . --pretty
```

The inventory command is read-only and returns a repository-relative JSON index. Confirm it identifies
the current directory as a Mule project. Do not commit its output unless the project intentionally
maintains that artifact.

## 7. Establish the operational application map

Inspect the project's flows, deployment files, and Anypoint application metadata before asking for
names. Record project-specific operational context in `AGENTS.md` or an existing project-owned
runbook, not in `.agents/skills/mule-ops/SKILL.md`.

Capture only when evidenced and useful:

1. entry application and participating Mule applications;
2. role of each application without assuming a Process/System pair;
3. dependency edges and correlation propagation;
4. normal analysis environment and reporting timezone;
5. scheduler, batch, queue, retry, and deployment constraints relevant to operations.

Ask the user only for values that cannot be established from repository or authorized Anypoint
evidence. Keep customer or organization identity out of reusable skills and examples.

## 8. Generate project agent context

Run the inventory from Step 6, then inspect `pom.xml`, Mule XML, RAML/OAS, DataWeave, MUnit,
configuration, and deployment files. Use that evidence to fill
`$MULE_SKILLS_TMP/templates/AGENTS.md` and write `AGENTS.md` at the project root.

Derive when possible:

- what the application does and its API layer (Experience, Process, System, or another pattern);
- external systems and companion Mule applications;
- environments and deployment target;
- key flows, schedules, configuration keys, error handling, and operational constraints.

Remove irrelevant template sections and placeholders. Never copy assumptions, credentials, tokens,
tenant IDs, customer names from unrelated examples, or unsupported claims into the generated file.
If a business or customer name is necessary for project context, confirm it with the user first.

## 9. Generate host-specific context files

Always create `AGENTS.md`. Generate the following only for agents the project actually uses:

- `GEMINI.md` from `templates/GEMINI.md`
- `CLAUDE.md` from `templates/CLAUDE.md`

Fill only evidence-backed sections. Remove optional sections that do not apply, and do not ask for
connector, organization, or environment details unless current project evidence makes them relevant.

## 10. Update `.gitignore`

Ensure shared agent configuration is trackable when selected, even if the project has a broad hidden-file
ignore rule:

```gitignore
!.agents/
!.agents/**
!.codex/
!.codex/**
!.cursor/
!.cursor/**
!.vscode/
!.vscode/**
!.mcp.json
```

Add this local binding to `.gitignore`:

```gitignore
.anypoint-connect.json
```

Add exceptions only for directories the setup actually created. Do not weaken unrelated ignore rules.

## 11. Validate and review

Run these checks before committing:

```bash
python3 .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py . --pretty
python3 .agents/skills/document-mulesoft-project/scripts/audit_documentation.py AGENTS.md
git diff --check
git status --short
git diff -- .agents AGENTS.md GEMINI.md CLAUDE.md .codex .cursor .vscode .mcp.json .gitignore
```

Also verify:

- every copied skill has a valid `SKILL.md` with `name` and `description` frontmatter;
- no unresolved `<!-- PLACEHOLDER -->` or `<YOUR_...>` values remain in generated project files;
- no secrets, credentials, customer names, or unrelated client details were introduced;
- existing project content was not overwritten accidentally;
- the configured MCP client lists all selected servers successfully.

## 12. Clean up the temporary clone

Resolve and validate the temporary path before removing it:

```bash
test -n "$MULE_SKILLS_TMP" && test -d "$MULE_SKILLS_TMP/.git" && rm -rf -- "$MULE_SKILLS_TMP"
unset MULE_SKILLS_TMP
```

This removes only the isolated clone created in Step 2.

## 13. Commit when authorized

Show the user the validation results and diff summary. If the setup request includes authorization to
commit, stage only the files created or intentionally updated by this setup and use a conventional commit:

```bash
git commit -m "feat: add MuleSoft agent skills and tooling"
```

Do not push unless the user explicitly requested a push.

## 14. Report the result

Report:

1. installed skills and workflow;
2. generated project context files;
3. configured MCP host and exact config path;
4. Anypoint profile status without revealing profile or organization names;
5. validation results;
6. files changed and commit hash, if committed;
7. any values or optional integrations still requiring user action.

## Updating an existing installation

1. Review `git status` and preserve local edits.
2. Clone the latest repository into a new `mktemp` directory as in Step 2.
3. Compare the installed skills, workflow, and MCP templates with the new versions.
4. Update all five skills and `workflows/build.md` after reviewing their diffs.
5. If an installed skill contains project identity or topology, move that context into `AGENTS.md`
   or a project-owned runbook before replacing the reusable skill.
6. Review MCP package version changes and upstream release notes before changing pinned versions.
7. Never overwrite generated `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` with templates. Refresh their
   content from current project evidence instead.
8. Repeat Steps 11–14.
