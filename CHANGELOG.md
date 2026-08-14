# Changelog

## 1.0.2

Dependency refresh for safer Anypoint application management. No skill behavior or install-path
changes.

### Updated

- Pinned `anypoint-connect` to `0.9.1` across bundled MCP host configuration, installer guidance,
  and setup documentation. This release supports narrow application-settings and lifecycle updates,
  corrected deployment detail handling, and history-aware rollback selection.

## 1.0.1

Manifest hygiene, and validation for the packaging rules that were documented but not
enforced. No skill, MCP, or install-path changes.

### Removed

- **`displayName` from both manifests.** It is in neither the marketplace nor the
  plugin-manifest schema. Both schemas leave `additionalProperties` unset, so it validated
  rather than erroring — but the CLI ignores it and renders `name`, which is why the plugin
  always listed as `mule-skills@mule-skills` despite declaring `"Mule Skills"`. A field that
  looks load-bearing but does nothing is worse than an absent one. The validator now rejects
  it so it cannot come back.

### Added

- **The marketplace-name rule is now enforced.** `1.0.0` settled that the catalog takes the
  repository's name, because marketplace names are global per user and a shared catalog name
  silently displaces another repository's marketplace. That reasoning lived only in prose;
  `validate_repository.py` now fails if the marketplace name and the repository name in
  `plugin.json` disagree.
- **Cross-manifest drift checks.** Only `version` was compared between the two manifests.
  `license`, `repository`, and `homepage` are now compared too, and the marketplace entry's
  `author` must match the marketplace `owner`.
- **Entry discovery metadata is required.** A marketplace browser reads the entry in
  `marketplace.json`, not `plugin.json`, so `description`, `license`, `repository`,
  `category`, and `tags` must all be present on the entry. The entry also now declares
  `author`, which it previously omitted.
- **Plugin manifest completeness.** `description`, `license`, `repository`, and `homepage`
  are now required rather than assumed.
- **A reintroduced `"skills"` key is rejected.** With `source: "./"`, `skills/` is scanned by
  default and an explicit declaration can replace that scan rather than extend it, silently
  dropping skills.
- Six tests asserting each new check actually rejects. A check that never fires is
  indistinguishable from no check at all. The suite goes from 16 tests to 22.

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

Both the plugin and the marketplace are named `mule-skills`, so the install reads
`/plugin install mule-skills@mule-skills`.

The repetition is deliberate, and it is the safe choice. Marketplace names are global per user:
adding a second marketplace under a name already registered silently replaces the first, and the
plugins installed from the replaced catalog stop resolving — they report `failed to load` and
`plugin details` cannot find them. Because this repository publishes its own catalog rather than
being listed in a shared one, the only name guaranteed not to collide with another catalog is the
repository's own.

A publisher-scoped name such as an npm scope would read better in isolation, but it is exactly the
name that collides: every repository publishing its own catalog under one publisher name would
overwrite the previous one. That trade is only worth making behind a single shared catalog
repository that lists each plugin with a `github` source, which is the path to take if these ever
need to install from one marketplace.

Note that a marketplace name does not have to match the repository path typed in
`/plugin marketplace add` — the two are separate identifiers — so this repetition is a choice about
collision safety, not a constraint.

### Other

- Added `LICENSE` (MIT). The README previously said "private repository — internal use only", which
  contradicted public marketplace distribution.
- The repository validator now checks the plugin and marketplace manifests, skill portability, and
  sibling-skill references. CI runs `claude plugin validate --strict` alongside it.
