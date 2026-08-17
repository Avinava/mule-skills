# Agent installation runbook

> **Instructions for AI coding agents.** Follow this from the root of the Mule repository being
> configured. Inspect first, preserve existing work, and ask only for decisions or facts you cannot
> derive safely.

## Safety rules

- Treat every existing file and uncommitted change as user-owned. Preserve unrelated edits.
- Never delete or rename existing `.agent/`, `.agents/`, `.codex/`, `.cursor/`, `.github/`, or
  `.vscode/` directories to make installation easier.
- Compare existing skills, templates, and MCP configuration before replacing or merging them. Do not
  overwrite customized files.
- Keep the reusable skills neutral. Project identity and topology belong in `AGENTS.md`, never under
  `.agents/skills/`.
- Never write credentials, tokens, client secrets, tenant IDs, secret-property values, private keys,
  or raw payloads into project guidance or MCP configuration.
- Configure only the hosts the user actually uses. Get approval before editing files outside the
  repository.
- Show validation results and the final diff before committing. Push only when explicitly requested.

## 1. Inspect the target repository

Confirm this is a Mule 4 project and record what is already present:

```bash
ls -a
test -f pom.xml && test -f mule-artifact.json && echo "mule project"
ls -a .agents .agents/skills .codex .vscode .github 2>/dev/null
cat .agents/skills/.mule-skills-version 2>/dev/null
git status --short
```

If `.mule-skills-version` exists, this is an upgrade. If skills exist without it, they were
installed by hand — diff before replacing.

Ask the user which agent hosts they use if the repository does not make it obvious.

## 2. Prefer the script

If a shell is available, this replaces steps 3 and 4 entirely. Prefer cloning, so the user can read
the script before it runs:

```bash
MULE_SKILLS_TMP="$(mktemp -d)"
git clone --depth 1 https://github.com/Avinava/mule-skills.git "$MULE_SKILLS_TMP/mule-skills"
"$MULE_SKILLS_TMP/mule-skills/install/install.sh" --target . --dry-run
```

Only if `git` is unavailable, and after telling the user you are piping a remote script into a
shell:

```bash
curl -fsSL https://raw.githubusercontent.com/Avinava/mule-skills/main/install/install.sh \
  | bash -s -- --dry-run
```

Show the user the dry-run output, then re-run without `--dry-run`. Pass `--hosts` when the user has
named their hosts, for example `--hosts codex,vscode`. See
[install-other-agents.md](install-other-agents.md) for all options. Then skip to step 5.

Claude Code users should not use the script at all — direct them to
[install-claude-code.md](install-claude-code.md) for the plugin install.

## 3. Install the skills by hand

Only when no shell is available, or the script failed.

```bash
MULE_SKILLS_TMP="$(mktemp -d)"
git clone --depth 1 https://github.com/Avinava/mule-skills.git "$MULE_SKILLS_TMP/mule-skills"
mkdir -p .agents/skills
```

Copy all six skills:

| Skill | Contents |
| --- | --- |
| `mule-docs` | `SKILL.md`, metadata, references, inventory script, documentation audit |
| `mule-development` | `SKILL.md`, metadata, invariant classes, checklist, embedded-expression checker |
| `mule-troubleshooting` | `SKILL.md`, metadata |
| `mule-ops` | `SKILL.md`, metadata |
| `mule-review` | `SKILL.md`, metadata, review domains, finding policy |
| `mule-build` | `SKILL.md`, metadata |

```bash
for skill in mule-build mule-development mule-docs mule-ops mule-review mule-troubleshooting; do
  rm -rf ".agents/skills/$skill"
  cp -R "$MULE_SKILLS_TMP/mule-skills/skills/$skill" .agents/skills/
done
```

**Upgrading from an earlier layout.** These were renamed, and the build workflow became a skill.
Remove the superseded copies so the agent does not load two versions:

```bash
rm -rf .agents/skills/document-mulesoft-project   # now mule-docs
rm -rf .agents/skills/review-mulesoft-project     # now mule-review
rm -f  .agents/workflows/build.md                 # now the mule-build skill
rmdir  .agents/workflows 2>/dev/null || true
```

## 4. Merge MCP configuration for selected hosts only

The source configurations are in the clone under `install/hosts/`. **Merge, never replace** — read
the existing file first and add only the server keys it lacks.

| Host | Destination | Source | Shape |
| --- | --- | --- | --- |
| Codex | `.codex/config.toml` | `install/hosts/codex/config.toml` | `[mcp_servers.<name>]` tables |
| VS Code, Copilot Chat | `.vscode/mcp.json` | `install/hosts/vscode/mcp.json` | `servers` object with `"type": "stdio"` |
| Claude Code, Copilot CLI, Gemini | `.mcp.json` | `install/hosts/mcp.json` | `mcpServers` object |

If the destination already defines a server with the same name, leave it alone and tell the user.

These pins were verified on **2026-08-18**:

| Package | Source | Node.js |
| --- | --- | ---: |
| [`@sfdxy/anypoint-connect@0.11.0`](https://registry.npmjs.org/@sfdxy%2Fanypoint-connect/0.11.0) | [`Avinava/anypoint-connect`](https://github.com/Avinava/anypoint-connect) | `>=20.0.0` |
| [`@sfdxy/mule-build@2.1.0`](https://registry.npmjs.org/@sfdxy%2Fmule-build/2.1.0) | [`Avinava/mule-build`](https://github.com/Avinava/mule-build) | `>=20.19.0` |
| [`@sfdxy/mule-lint@1.25.0`](https://registry.npmjs.org/@sfdxy%2Fmule-lint/1.25.0) | [`Avinava/mule-lint`](https://github.com/Avinava/mule-lint) | `>=20.0.0` |

Use Node.js `>=20.19.0` to satisfy all three. Do not change a pin without reviewing the linked
source repository and its release notes.

## 5. Verify what landed

```bash
for skill in mule-build mule-development mule-docs mule-ops mule-review mule-troubleshooting; do
  test -f ".agents/skills/$skill/SKILL.md" || echo "MISSING: $skill"
done
test -f .agents/skills/mule-docs/scripts/inventory_mule_project.py
test -f .agents/skills/mule-development/scripts/check_embedded_expressions.py
```

Run the bundled tools against this project to prove they work:

```bash
python3 .agents/skills/mule-docs/scripts/inventory_mule_project.py . --pretty
python3 .agents/skills/mule-development/scripts/check_embedded_expressions.py .
```

The inventory is read-only. The checker exits `0` when clean and `1` on findings; report findings
rather than fixing them as part of installation.

Then verify MCP per host: `codex mcp list`, `copilot mcp list`, or reload VS Code and inspect its
MCP server list.

## 6. Hand off to project setup

Create or reconcile `AGENTS.md` and any host instruction files, and reconcile `.gitignore`, by
following [project-setup.md](project-setup.md). That is where the judgment lives — this runbook only
places files.

Do not authenticate `anypoint-connect` as part of installation. Report that runtime evidence needs it
and point the user at [anypoint-access.md](anypoint-access.md); login, global install, and profile
selection all need the user's own approval.

## 7. Clean up and report

```bash
rm -rf "$MULE_SKILLS_TMP"
git status --short
git diff
```

Report: which skills were installed or upgraded, which hosts were configured, which files were left
untouched because they already existed, and any verification finding. Commit only when the user
authorizes it. Never push unless explicitly asked.
