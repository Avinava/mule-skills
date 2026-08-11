# GitHub Copilot Instructions

Read `AGENTS.md` for the current project's evidence-backed architecture, commands, constraints, and
operational context. Current source and repository instructions are authoritative over reusable
examples.

## MuleSoft workflows

When a task matches one of these workflows, read and follow its installed instructions:

- development: `.agents/skills/mule-development/SKILL.md`
- troubleshooting and RCA: `.agents/skills/mule-troubleshooting/SKILL.md`
- runtime health and operations: `.agents/skills/mule-ops/SKILL.md`
- documentation: `.agents/skills/document-mulesoft-project/SKILL.md`
- change, project, or release-readiness review:
  `.agents/skills/review-mulesoft-project/SKILL.md`
- validation, packaging, or an explicitly requested release: `.agents/workflows/build.md`

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
