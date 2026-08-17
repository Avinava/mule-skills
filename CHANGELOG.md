# Changelog

## 1.2.0

Pin refresh across all three MCP servers, each of which now publishes its own documentation site. No
skill behavior or install-path changes.

### Updated

- **`mule-lint` to `1.25.0`.** Its `docs/` tree ships inside the package and is served over MCP, so the
  release matters to an agent rather than only to a reader: a four-backtick code fence closed with three
  had been swallowing a whole section of the rules catalog, and the rule-family table claimed 13 families
  summing to 75 against a stated total of 82. Counts now come from the registry — 82 rules, 18 prefixes,
  15 categories.
- **`mule-build` to `2.1.0`.** Adds three packaged documentation resources —
  `mule-build://docs/prerequisites`, `mule-build://docs/troubleshooting`, and `mule-build://docs/cli` —
  so the prerequisites and failure modes that were previously undocumented are readable by an agent
  offline. `mule-build.yaml.example` now ships too; it had been excluded from the package while the README
  inlined a second sample that had drifted from it.
- **`anypoint-connect` to `0.11.0`.** Ships the `LICENSE` that was listed in `files` but did not exist,
  documents `compare_environments` (55 documented against 56 registered), and corrects `engines.node`
  from an untested `>=18.0.0` to `>=20.0.0`. The Node requirement in
  [docs/agent-install.md](docs/agent-install.md) follows.
- Each server's own documentation is now linked from [docs/mcp-servers.md](docs/mcp-servers.md) and
  [docs/index.md](docs/index.md), which previously pointed only at repository roots.

`validate_pin_consistency` requires every one of the thirty-odd pin references across the plugin
configuration, three host forms, the installer, the README, five documentation pages, and the readiness
reference to agree with `.mcp.json`, so this bump is necessarily atomic.

## 1.1.0

Runtime evidence now has an explicit access gate, and the documentation is published as a site.

### Added

- **An Anypoint readiness gate.** `anypoint-connect` is the only server that needs authentication,
  and until now nothing in the skill text checked for it: `mule-ops` went straight to
  `get_log_stats`, so an unconfigured host produced tool errors in the middle of a workflow. A
  shared reference, `skills/mule-ops/references/anypoint-readiness.md`, defines a `whoami` and
  `list_environments` probe, six access states, and the choices offered when the state is not
  `Ready` — set it up, supply exported logs and metrics, or continue with repository-only evidence
  and a labeled gap. `mule-ops`, `mule-troubleshooting`, `mule-review`, and the publish and deploy
  actions in `mule-build` route through it.

  It is a reference rather than a seventh skill on purpose. Readiness is a step inside four
  workflows, not a task a user asks for, and a skill the agent has to select first would be one more
  thing to miss. The states are separated because their fixes differ: telling someone to log in when
  their host never started the server wastes the exchange.

  A collection tool is explicitly not a probe. An empty log result is indistinguishable from an
  unauthenticated one, and that ambiguity is what turned missing access into false findings.

- **User-supplied evidence is a first-class path.** The reference states which artifacts to ask for
  per gap and the metadata that makes them usable — application, environment, window, timezone, log
  level, truncation. Exports enter as user-provided with stated coverage and never become `Observed`,
  because absence of an entry in a filtered or truncated export is not evidence of absence.

- **A documentation site**, built with MkDocs Material from `docs/` and deployed by GitHub Actions to
  <https://avinava.github.io/mule-skills/>. New pages: a landing page, `anypoint-access.md` with the
  full setup, verification, and failure-mode runbook, `mcp-servers.md`, `skills.md`, and `faq.md`.
  `docs/` stays the single source and remains readable on GitHub; nothing is generated or duplicated.

- **Three validator rules, one rejecting test each** (22 tests to 28):
  - `validate_pin_consistency` — every `@sfdxy/…@version` in the README, `docs/`, `install/`, and
    `skills/` must match `.mcp.json`. The pins appeared in eleven places across five files, so a
    partial bump could leave a user installing one version and reading instructions for another.
  - `validate_site_nav` — no page under `docs/` may be orphaned from the site, and no nav entry may
    point at a missing file.
  - `validate_anypoint_readiness` — the four gated skills must route through the shared reference,
    and the reference must keep all six states and both probe calls.

### Changed

- `docs/project-setup.md` keeps a short pointer where the Anypoint runbook used to be; the six links
  it had into `install/templates/` became absolute GitHub URLs so they resolve both on GitHub and on
  the site.
- `assets/banner.svg` moved to `docs/assets/banner.svg` so the README and the site share one file.
- Both manifests point `homepage` at the site. `repository` still points at GitHub.
- `install/install.sh` now suggests verifying with `auth status` rather than only running
  `auth login`, and CI builds the site with `mkdocs build --strict` on every pull request.

## 1.0.3

Dependency refresh for safer Anypoint application lifecycle management. No skill behavior or
install-path changes.

### Updated

- Pinned `anypoint-connect` to `0.10.0` across bundled MCP host configuration, installer guidance,
  and setup documentation. This release adds deployment-ID-bound application deletion, an extra
  production acknowledgement, and post-delete verification.

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
