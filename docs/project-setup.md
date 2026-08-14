# Project setup

Installing the skills places files. This is the part that needs judgment: giving the skills accurate,
evidence-backed context about *your* project. Do this once after installing, and revisit it when the
architecture changes.

Everything here applies to all hosts, including Claude Code plugin installs.

## Create or reconcile `AGENTS.md`

`AGENTS.md` is the shared project context every skill reads. Build it from current repository
evidence — the inventory plus applicable `pom.xml`, `mule-artifact.json`, Mule XML, RAML/OAS,
DataWeave, MUnit, configuration, deployment, CI, and existing documentation.

Start from [`install/templates/AGENTS.md`](../install/templates/AGENTS.md), or run the inventory
first to route your reading:

```bash
python3 <skills-root>/mule-docs/scripts/inventory_mule_project.py . --pretty
```

`<skills-root>` is `${CLAUDE_PLUGIN_ROOT}/skills` under the Claude Code plugin and `.agents/skills`
when vendored.

Capture only what is evidenced and useful:

- purpose, application role, and system boundary;
- key triggers, flows, collaborators, and outcomes;
- contract and delivery semantics;
- configuration keys, without values;
- error, retry, queue, batch, scheduler, timeout, concurrency, and state behavior;
- build, test, deployment, review, and operational guidance;
- verified constraints, decisions, and unresolved gaps.

Preserve correct existing guidance. Remove unused template sections and every unresolved
placeholder. Never copy names, examples, values, incidents, or assumptions from another project.

### Optional business-context checkpoint

After technical inspection, surface only questions whose answers would materially improve the
guidance. Do not block setup or documentation on them.

- Ask no more than five questions in one batch.
- State that every item and the entire checkpoint can be skipped.
- Where practical, offer two to four concise choices plus `Other (please specify)` and
  `Not sure / Skip`.
- Record answers as user-provided context, not as proof of runtime behavior.
- If the user skips, continue with verified technical facts and keep material gaps visible.

Example:

```text
Optional business context — answer any item or reply "skip":
1. Who primarily uses this guidance?
   A) Mule developers  B) Support/operators  C) API consumers  D) Mixed audience
   E) Other (please specify)  F) Not sure / Skip
```

## Host instruction files

`AGENTS.md` owns the shared project facts. Host files should point at it and carry only
host-specific directives — keep them compact and do not duplicate the inventory.

| Host | File | Template |
| --- | --- | --- |
| Claude Code (plugin install) | not needed for routing; add `CLAUDE.md` only for project-specific directives | [`CLAUDE.md`](../install/templates/CLAUDE.md) |
| Claude Code (vendored install) | `CLAUDE.md` | [`CLAUDE.md`](../install/templates/CLAUDE.md) |
| GitHub Copilot | `.github/copilot-instructions.md` | [`copilot-instructions.md`](../install/templates/copilot-instructions.md) |
| Gemini | `GEMINI.md` | [`GEMINI.md`](../install/templates/GEMINI.md) |
| Codex | `AGENTS.md` only | [`AGENTS.md`](../install/templates/AGENTS.md) |

Reconcile an existing file rather than overwriting it, and remove the project-name placeholder before
saving. See the official
[Claude Code project-instruction documentation](https://docs.anthropic.com/en/docs/claude-code/memory)
and
[GitHub Copilot repository-instruction documentation](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions-in-your-ide/add-repository-instructions-in-your-ide).

## Optional Anypoint access

Only `anypoint-connect` needs authentication. Skip this if you only need documentation, development,
lint, build, or static review workflows — the other two servers work with no credentials.

Check for an existing authenticated profile first, and get approval before a global install:

```bash
npm install -g @sfdxy/anypoint-connect@0.9.1
anc config init
anc auth login
anc auth status
```

With multiple organizations, use a neutral local profile identifier rather than an organization or
customer name:

```bash
anc config init --profile org-a
anc auth login --profile org-a
anc config use org-a
anc auth status
```

`anc config use` creates `.anypoint-connect.json`. It binds a machine-local profile rather than
storing credentials, but it can reveal local organization labeling — add it to `.gitignore`, and do
not report the selected profile or organization name.

## Reconcile `.gitignore`

Only relevant to vendored installs. If a broad hidden-file rule would exclude the installed files,
add exceptions for the paths this setup created — and nothing more:

```gitignore
!.agents/
!.agents/**
```

Add `.anypoint-connect.json` to `.gitignore` if you configured an Anypoint profile.

## Validate

```bash
python3 <skills-root>/mule-docs/scripts/inventory_mule_project.py . --pretty
python3 <skills-root>/mule-docs/scripts/audit_documentation.py AGENTS.md
```

The audit checks documentation for exposed secrets, unsupported claims, broken links, and unsafe
Mermaid directives. Resolve findings before committing.

## Commit

Show the validation results and the final diff first. Commit only when the user authorizes it, and
push only when explicitly requested.
