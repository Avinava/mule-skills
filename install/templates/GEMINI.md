# <!-- PROJECT_NAME --> — Gemini Instructions

Read `AGENTS.md` for the current project's evidence-backed context. Repository instructions and the
current source are authoritative over reusable examples.

<!-- SKILLS_LOCATION -->

## Routing

| Task | Skill |
| --- | --- |
| Mule source, DataWeave, connector, or MUnit changes | `mule-development` |
| Incident diagnosis and root-cause analysis | `mule-troubleshooting` |
| Runtime health and operations | `mule-ops` |
| Documentation creation and targeted refreshes | `mule-docs` |
| Change, PR, project, or release-readiness review | `mule-review` |
| Validation, packaging, or an explicitly requested release | `mule-build` |

## Development

Use `mule-development` for Mule source changes and complete its post-development checklist. Preserve
contracts, delivery semantics, error outcomes, privacy boundaries, and project conventions.

## Troubleshooting and operations

Use `mule-troubleshooting` for RCA and `mule-ops` for runtime health analysis. Separate observations,
hypotheses, confirmed causes, and unresolved gaps.

## Build

Use `mule-build`, or the project's configured Mule build tools. Treat versioning, changelog updates,
tags, deployment, and test skipping as explicit release choices rather than automatic build steps.

## Review

Use `mule-review` for change, PR, project, and release-readiness reviews. Report findings and
remediation options without changing source or PR state unless explicitly requested.

## Privacy

Do not introduce identity, topology, payloads, endpoints, schedules, volumes, or incident details
from another project. Never expose secrets, tenants, private hosts, personal data, or raw production
payloads.
