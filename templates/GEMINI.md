# <!-- PROJECT_NAME --> — Gemini Instructions

Read `AGENTS.md` for the current project's evidence-backed context. Repository instructions and the
current source are authoritative over reusable examples.

When a workflow below applies, read its installed instructions under `.agents/` before acting.

## Development

Read `.agents/skills/mule-development/SKILL.md` for Mule source changes and complete its
post-development checklist. Preserve contracts, delivery semantics, error outcomes, privacy
boundaries, and project conventions.

## Troubleshooting and operations

Read `.agents/skills/mule-troubleshooting/SKILL.md` for RCA and
`.agents/skills/mule-ops/SKILL.md` for runtime health analysis. Separate observations, hypotheses,
confirmed causes, and unresolved gaps.

## Build

Read `.agents/workflows/build.md` or use configured Mule build tools. Treat versioning, changelog
updates, tags, deployment, and test skipping as explicit release choices rather than automatic build
steps.

## Documentation

Read `.agents/skills/document-mulesoft-project/SKILL.md` for documentation creation and targeted
refreshes.

## Review

Read `.agents/skills/review-mulesoft-project/SKILL.md` for change, PR, project, and
release-readiness reviews. Report findings and remediation options without changing source or PR
state unless explicitly requested.

## Privacy

Do not introduce identity, topology, payloads, endpoints, schedules, volumes, or incident details
from another project. Never expose secrets, tenants, private hosts, personal data, or raw production
payloads.
