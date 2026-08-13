# Changelog

## 1.0.0

First packaged release. The repository is now both a Claude Code plugin and a plugin marketplace, so
installing it no longer requires an agent to execute a copy runbook.

### Install

- **Claude Code:** `/plugin marketplace add Avinava/mule-skills` then
  `/plugin install mule-skills@mule-skills`. Skills and the three pinned MCP servers ship with the
  plugin.
- **Other hosts:** `install/install.sh` vendors the skills into `.agents/skills/`, detects which
  hosts you use, and merges MCP configuration without overwriting existing entries. It is idempotent
  and supports `--dry-run`.
- **Any agent:** the copy-paste prompt still works and now targets
  [`docs/agent-install.md`](docs/agent-install.md).

### Skills renamed

The build workflow became a skill, so all six are now discovered the same way on every host.

| Was | Now |
| --- | --- |
| `document-mulesoft-project` | `mule-docs` |
| `review-mulesoft-project` | `mule-review` |
| `workflows/build.md` | `mule-build` |
| `mule-development` | unchanged |
| `mule-ops` | unchanged |
| `mule-troubleshooting` | unchanged |

Update any saved prompts that name the old skills. `install/install.sh` and
`docs/agent-install.md` both remove the superseded directories on upgrade.

### Skill portability

Skills referenced their scripts through a hardcoded `.agents/skills/...` path, which does not exist
under a plugin install. They now use `<skill-root>` and `<skills-root>` placeholders with a
resolution note, so the same file works in both layouts. The repository validator fails the build if
a hardcoded path or an unknown sibling-skill reference reappears.

### Repository layout

| Was | Now |
| --- | --- |
| `workflows/` | `skills/mule-build/` |
| `mcp/` | `install/hosts/` |
| `templates/` | `install/templates/` |
| `scripts/` | `tools/` |
| `SETUP.md` (416 lines) | `docs/`, with `SETUP.md` kept as a redirect |

`workflows/` was vacated because Claude Code reserves that directory for JavaScript workflow scripts.

### Naming

The marketplace and the plugin are both named `mule-skills`, so the install reads
`mule-skills@mule-skills`. This is deliberate: it matches
[`document-design-system`](https://github.com/Avinava/document-design-system), which already ships
one repository as one plugin with its own self-named marketplace. Consistency across repositories
beats an owner-scoped marketplace name here, and renaming a published marketplace is expensive —
users must remove it, which uninstalls its plugins, then re-add it.

If a single catalog spanning several repositories is ever wanted, the cheap path is a new
`Avinava/claude-plugins` repository whose `marketplace.json` lists each plugin with a `github`
source. That needs no change to this repository or to any existing one.

### Other

- Added `LICENSE` (MIT). The README previously said "private repository — internal use only", which
  contradicted public marketplace distribution.
- The repository validator now checks the plugin and marketplace manifests, skill portability, and
  sibling-skill references. CI runs `claude plugin validate --strict` alongside it.
