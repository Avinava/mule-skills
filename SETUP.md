# MuleSoft Skills — Installation and Reconciliation Runbook

> **Instructions for AI coding agents:** follow this runbook from the root of the Mule repository
> being configured. Inspect first, preserve existing work, and ask only for decisions or facts that
> cannot be derived safely.

## Intended result

Install or reconcile:

- five reusable skills under `.agents/skills/`;
- the Mule build workflow under `.agents/workflows/`;
- MCP configuration for only the selected agent host;
- an evidence-backed project `AGENTS.md`;
- optional `CLAUDE.md`, `.github/copilot-instructions.md`, or `GEMINI.md` files only when those
  hosts are used.

Do not commit or push unless the user authorizes it.

## Safety rules

- Treat every existing file and uncommitted change as user-owned. Preserve unrelated edits.
- Never delete or rename existing `.agent/`, `.agents/`, `.codex/`, `.cursor/`, `.github/`, or
  `.vscode/` directories to make installation easier.
- Compare existing skills, workflows, templates, and MCP configuration before replacing or merging
  them. Do not blindly overwrite customized files.
- Keep reusable skills neutral. Project identity and topology belong in `AGENTS.md` or a
  project-owned runbook, not under `.agents/skills/`.
- Never write credentials, tokens, client secrets, tenant IDs, secret-property values, private keys,
  or raw payloads into project guidance or MCP configuration.
- Configure only the host the user actually uses. Obtain approval before editing files outside the
  repository.
- Show validation results and the final diff before committing. Push only when explicitly requested.

## Verified toolchain

These pins were verified on **2026-08-12**:

| Component | Pinned version | Node.js requirement |
| --- | ---: | ---: |
| `@sfdxy/anypoint-connect` | `0.9.0` | `>=18.0.0` |
| `@sfdxy/mule-build` | `2.0.0` | `>=20.19.0` |
| `@sfdxy/mule-lint` | `1.24.1` | `>=20.0.0` |

Use Node.js `>=20.19.0` to satisfy all three. The repository pins package versions so upgrades are
deliberate; review upstream release notes before changing them.

## 1. Inspect the target repository

Before modifying anything:

1. Resolve the repository root and read `AGENTS.md` plus any host-specific instructions.
2. Run `git status --short` and record existing changes.
3. Confirm this is a Mule 4 application or Mule-focused repository using direct evidence such as
   Mule XML, DataWeave, RAML/OAS, MUnit, `mule-artifact.json`, Mule Maven packaging, or Mule-specific
   tooling and fixtures.
4. Check that `git`, `python3`, `node`, `npm`, and `npx` are available.
5. Confirm `node --version` satisfies `>=20.19.0`.
6. Identify the agent host in use and whether Anypoint runtime access is required.

For a deployable Mule application, inspect `pom.xml` and `mule-artifact.json`. For a partial fixture
or Mule-focused tooling repository, record that boundary instead of presenting it as deployable. If
there is no relevant Mule evidence, stop and explain what was checked.

## 2. Clone this repository into an isolated directory

Use a unique temporary directory; never reuse a fixed path:

```bash
MULE_SKILLS_TMP="$(mktemp -d "${TMPDIR:-/tmp}/mule-skills.XXXXXX")"
git clone --depth 1 https://github.com/Avinava/mule-skills.git "$MULE_SKILLS_TMP"
```

Keep `MULE_SKILLS_TMP` until cleanup. If the clone fails, leave the target repository unchanged and
ask the user to confirm access.

## 3. Install or reconcile the skills and workflow

Create only the shared directories that are missing:

```bash
mkdir -p .agents/skills .agents/workflows
```

The complete shared set is:

| Skill | Required content |
| --- | --- |
| `document-mulesoft-project` | `SKILL.md`, metadata, references, inventory script, documentation audit |
| `mule-development` | `SKILL.md`, metadata, post-development checklist |
| `mule-troubleshooting` | `SKILL.md`, metadata |
| `mule-ops` | `SKILL.md`, metadata |
| `review-mulesoft-project` | `SKILL.md`, metadata, review domains, finding policy |

For a new installation, copy all five skills and the workflow:

```bash
cp -R "$MULE_SKILLS_TMP/skills/document-mulesoft-project" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-development" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-troubleshooting" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/mule-ops" .agents/skills/
cp -R "$MULE_SKILLS_TMP/skills/review-mulesoft-project" .agents/skills/
cp "$MULE_SKILLS_TMP/workflows/build.md" .agents/workflows/build.md
```

For an existing installation:

1. Compare each installed skill and workflow with the cloned source.
2. Preserve intentional reusable changes that still belong in a shared skill.
3. Move project identity, topology, endpoints, operating values, and local constraints into
   `AGENTS.md` or a project-owned runbook.
4. Reconcile or replace the reusable files only after reviewing their diffs.
5. Do not overwrite generated project context files with templates.

Codex reads repository skills from `.agents/skills/` in directories from the current working
directory up to the repository root. It detects changes automatically; restart Codex if a new skill
does not appear. See the official [Codex skills documentation](https://developers.openai.com/codex/skills/).

## 4. Configure the selected MCP host

The MCP templates contain no credentials. They launch the three pinned packages with `npx`:

| Template | Use |
| --- | --- |
| `mcp/.codex/config.toml` | Project-scoped Codex configuration |
| `mcp/.vscode/mcp.json` | VS Code and GitHub Copilot Chat configuration |
| `mcp/mcp.json` | Project `mcpServers` object for Claude Code, Copilot CLI, and compatible hosts |

### Codex

For a new project configuration:

```bash
mkdir -p .codex
cp "$MULE_SKILLS_TMP/mcp/.codex/config.toml" .codex/config.toml
codex mcp list
```

If `.codex/config.toml` already exists, merge the `[mcp_servers.*]` tables instead of replacing the
file. Project-scoped MCP configuration loads only for trusted projects. The ChatGPT desktop app,
Codex CLI, and Codex IDE extension share Codex MCP configuration for the same host. See the official
[Codex MCP documentation](https://developers.openai.com/codex/mcp/).

### GitHub Copilot in VS Code

For a new project configuration:

```bash
mkdir -p .vscode
cp "$MULE_SKILLS_TMP/mcp/.vscode/mcp.json" .vscode/mcp.json
```

If `.vscode/mcp.json` exists, merge the three entries into its `servers` object. Preserve unrelated
servers and settings. Repository-wide Copilot instructions are installed separately in Step 8.

For GitHub Copilot CLI, use the shared project `.mcp.json` instructions in the next section and
verify with `copilot mcp list`. GitHub-hosted Copilot agents and code review use repository settings
for hosted MCP access; do not copy local credentials or assume local MCP configuration applies to
GitHub-hosted runs.

### Claude Code and Copilot CLI

Both hosts can use a project-level `.mcp.json` containing the provided `mcpServers` object:

```bash
cp "$MULE_SKILLS_TMP/mcp/mcp.json" .mcp.json
```

If `.mcp.json` exists, merge the three entries into its `mcpServers` object instead of replacing the
file. Verify the active host:

```bash
# Claude Code
claude mcp list

# GitHub Copilot CLI
copilot mcp list
```

Claude Code asks for approval before using project-scoped servers from `.mcp.json`. Keep credentials
out of this shared file. See the official
[Claude Code MCP documentation](https://docs.anthropic.com/en/docs/claude-code/mcp).

### Other JSON-based hosts

Use `mcp/mcp.json` only when the selected host accepts an `mcpServers` object. Follow that host's
current documentation to choose the project or user configuration path. Display the destination and
proposed merge before modifying a user-level file, then obtain approval. Never assume that a generic
root `mcp.json` is discovered automatically.

After configuration, reload the selected host and verify all configured servers initialize. If a
server is intentionally omitted, report the resulting coverage gap rather than configuring another
host without permission.

## 5. Configure optional Anypoint access

Only `anypoint-connect` requires Anypoint authentication. Skip this step when the user needs only
local documentation, development, lint, build, or static review workflows.

First check whether `anc` and an authenticated profile already exist. Obtain approval before a
global npm installation:

```bash
npm install -g @sfdxy/anypoint-connect@0.9.0
anc config init
anc auth login
anc auth status
```

When multiple organizations are used, choose a neutral local profile identifier rather than an
organization or customer name:

```bash
anc config init --profile org-a
anc auth login --profile org-a
anc config use org-a
anc auth status
```

`anc config use` creates `.anypoint-connect.json`. It is a machine-specific profile binding, not a
credential file, but it can reveal local organization labeling. Add it to `.gitignore` and do not
report the selected profile or organization name.

## 6. Verify the installed resources

Run these existence checks:

```bash
test -f .agents/skills/document-mulesoft-project/SKILL.md
test -f .agents/skills/document-mulesoft-project/agents/openai.yaml
test -f .agents/skills/document-mulesoft-project/references/privacy-and-evidence.md
test -f .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py
test -f .agents/skills/document-mulesoft-project/scripts/audit_documentation.py
test -f .agents/skills/mule-development/SKILL.md
test -f .agents/skills/mule-development/agents/openai.yaml
test -f .agents/skills/mule-development/resources/post-development-checklist.md
test -f .agents/skills/mule-troubleshooting/SKILL.md
test -f .agents/skills/mule-troubleshooting/agents/openai.yaml
test -f .agents/skills/mule-ops/SKILL.md
test -f .agents/skills/mule-ops/agents/openai.yaml
test -f .agents/skills/review-mulesoft-project/SKILL.md
test -f .agents/skills/review-mulesoft-project/agents/openai.yaml
test -f .agents/skills/review-mulesoft-project/references/finding-policy.md
test -f .agents/skills/review-mulesoft-project/references/review-domains.md
test -f .agents/workflows/build.md
```

Then run the read-only inventory:

```bash
python3 .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py . --pretty
```

Treat its project classification as one signal. Reconcile it with direct source evidence, especially
for partial fixtures or Mule-focused tooling repositories. Do not commit inventory output unless the
project intentionally owns such an artifact.

## 7. Create or reconcile project context

Read the inventory plus applicable `pom.xml`, `mule-artifact.json`, Mule XML, RAML/OAS, DataWeave,
MUnit, configuration, deployment, CI, and existing documentation. Use current-project evidence to
create or update `AGENTS.md` from `templates/AGENTS.md`.

Capture only what is evidenced and useful:

- purpose, application role, and system boundary;
- key triggers, flows, collaborators, and outcomes;
- contract and delivery semantics;
- configuration keys without values;
- error, retry, queue, batch, scheduler, timeout, concurrency, and state behavior;
- build, test, deployment, review, and operational guidance;
- verified constraints, decisions, and unresolved gaps.

Preserve correct existing project guidance. Remove unused template sections and all unresolved
placeholders. Never copy names, examples, values, incidents, or assumptions from another project.

### Optional business-context checkpoint

After technical inspection, surface only questions whose answers would materially improve project
guidance. Do not block setup or documentation on them.

- Ask no more than five questions in one batch.
- State that every item and the entire checkpoint can be skipped.
- Where practical, offer two to four concise choices plus `Other (please specify)` and
  `Not sure / Skip`.
- Record answers as user-provided context, not proof of runtime behavior.
- If the user skips, continue with verified technical facts and keep only material gaps visible.

Example:

```text
Optional business context — answer any item or reply "skip":
1. Who primarily uses this guidance?
   A) Mule developers  B) Support/operators  C) API consumers  D) Mixed audience
   E) Other (please specify)  F) Not sure / Skip
```

## 8. Add host-specific guidance only when used

Always maintain `AGENTS.md`. Create or reconcile these files only for active hosts:

- Claude Code: create or reconcile `CLAUDE.md` from `templates/CLAUDE.md`.
- GitHub Copilot: create or reconcile `.github/copilot-instructions.md` from
  `templates/copilot-instructions.md`.
- Gemini: create or reconcile `GEMINI.md` from `templates/GEMINI.md`.

These files should point to `AGENTS.md` for project context and contain only host-specific
directives. Do not duplicate the project inventory or overwrite existing correct guidance.

Claude Code automatically reads project `CLAUDE.md` files. GitHub Copilot uses
`.github/copilot-instructions.md` as repository-wide instructions and can also use `AGENTS.md` on
supported surfaces. Keep both host files compact and let `AGENTS.md` own shared project facts.

For a new GitHub Copilot setup, the neutral template can be copied directly:

```bash
mkdir -p .github
cp "$MULE_SKILLS_TMP/templates/copilot-instructions.md" .github/copilot-instructions.md
```

Reconcile an existing file instead of overwriting it. For `CLAUDE.md` and `GEMINI.md`, adapt the
matching template to current-project evidence and remove the project-name placeholder before saving.
See the official [Claude Code project-instruction documentation](https://docs.anthropic.com/en/docs/claude-code/memory)
and [GitHub Copilot repository-instruction documentation](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide).

## 9. Reconcile `.gitignore`

Ensure only selected shared configuration remains trackable when a broad hidden-file rule would
otherwise exclude it. Add exceptions only for paths created by this setup:

```gitignore
!.agents/
!.agents/**
!.codex/
!.codex/**
!.vscode/
!.vscode/**
!.github/
!.github/copilot-instructions.md
!.mcp.json
```

When applicable, ignore the local Anypoint profile binding:

```gitignore
.anypoint-connect.json
```

Do not weaken unrelated ignore rules or add exceptions for unused hosts.

## 10. Validate the installation

Run:

```bash
python3 .agents/skills/document-mulesoft-project/scripts/inventory_mule_project.py . --pretty
python3 .agents/skills/document-mulesoft-project/scripts/audit_documentation.py AGENTS.md
git diff --check
git status --short
git diff -- .agents AGENTS.md CLAUDE.md GEMINI.md .codex .vscode .github .mcp.json .gitignore
```

Also verify:

- every installed skill has `name` and `description` frontmatter;
- `agents/openai.yaml` and every referenced resource or script were copied;
- the selected MCP host reports the configured servers or its configuration parses successfully;
- each selected host instruction file exists at its supported repository path;
- no unresolved template placeholders remain in generated files;
- no secrets, unrelated project identity, private hosts, raw payloads, or prior-project fingerprints
  were introduced;
- existing content and uncommitted work were not overwritten;
- required validation failures are reported rather than rerun with weaker options.

## 11. Review and commit only when authorized

Show the user:

1. installed or updated skills and workflow;
2. generated or reconciled project-context files;
3. configured MCP host and repository-relative configuration path;
4. Anypoint authentication status without profile or organization identity;
5. validation results and unresolved gaps;
6. exact files changed.

If committing is authorized, stage only intended setup files and use a conventional commit such as:

```bash
git commit -m "feat: add MuleSoft agent workflows"
```

Push only when explicitly requested.

## 12. Clean up the temporary clone

Resolve and validate the exact temporary path before removing it:

```bash
test -n "$MULE_SKILLS_TMP"
test -d "$MULE_SKILLS_TMP/.git"
rm -rf -- "$MULE_SKILLS_TMP"
unset MULE_SKILLS_TMP
```

This must remove only the isolated clone created in Step 2. If either validation fails, leave the
directory untouched and report it.
