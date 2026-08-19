# GitHub Copilot Instructions

Read `AGENTS.md` for the current project's evidence-backed architecture, commands, constraints, and
operational context. Current source and repository instructions are authoritative over reusable
examples.

## MuleSoft workflows

<!-- SKILLS_LOCATION -->

When a task matches one of these workflows, follow its instructions:

| Task | Skill |
| --- | --- |
| Mule production source, DataWeave, connector, or contract changes | `mule-development` |
| MUnit authoring, repair, fixtures, mocks, and assertions | `mule-testing` |
| Incident diagnosis and root-cause analysis | `mule-troubleshooting` |
| Runtime health and operations | `mule-ops` |
| Documentation creation and targeted refreshes | `mule-docs` |
| Change, project, or release-readiness review | `mule-review` |
| Validation, packaging, or an explicitly requested release | `mule-build` |

Load only the workflow and referenced resources relevant to the task. Preserve current-project
contracts, delivery semantics, error outcomes, privacy boundaries, and repository conventions.

## Evidence and validation

- Separate verified evidence, user-provided context, inference, recommendations, and unresolved
  gaps.
- Use focused validation for local changes and the complete repository-required gate for release
  readiness.
- Update affected contracts, tests, operations guidance, and documentation when behavior changes.
- Reviews and diagnosis are read-only by default. Do not modify source, post review comments,
  approve changes, tag, deploy, or release unless explicitly requested.

## Privacy

Never introduce identity, topology, payloads, endpoints, schedules, volumes, incidents, or numeric
tuning from another project. Never expose secrets, tenant identifiers, private hosts, personal data,
or raw production payloads.
