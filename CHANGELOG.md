# Changelog

## 1.0.0

First packaged release. The repository is now both a Claude Code plugin and a plugin marketplace, so
installing it no longer requires an agent to execute a copy runbook.

### Install

- **Claude Code:** `/plugin marketplace add Avinava/mule-skills` then
  `/plugin install mule-skills@sfdxy`. Skills and the three pinned MCP servers ship with the
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

The plugin is `mule-skills`; the marketplace is `sfdxy`. The install therefore reads
`/plugin install mule-skills@sfdxy`.

The two names are deliberately different. `@` means "from", so the identifier names the plugin and
the catalog it came from — naming both sides the same would read as a stutter and hide which side is
which. A marketplace is a catalog, so it takes the publisher's name: `sfdxy` is the npm scope behind
`@sfdxy/mule-build`, `@sfdxy/mule-lint`, and `@sfdxy/anypoint-connect`, the three MCP servers this
plugin ships, so the plugin and its tooling read as one publisher's work.

Marketplace names are global per user, and adding a second marketplace under an existing name
silently replaces the first, so a publisher-scoped name collides far less than a topical one. The
marketplace name deliberately does not have to match the repository path typed in
`/plugin marketplace add`; the two are separate identifiers.

This was worth settling before publication: renaming a marketplace afterwards forces every user to
remove it, which uninstalls the plugins installed from it, and then re-add it.

### Other

- Added `LICENSE` (MIT). The README previously said "private repository — internal use only", which
  contradicted public marketplace distribution.
- The repository validator now checks the plugin and marketplace manifests, skill portability, and
  sibling-skill references. CI runs `claude plugin validate --strict` alongside it.
