# <!-- PROJECT_NAME --> — Claude Instructions

Read `AGENTS.md` for the current project's evidence-backed context. Repository instructions and the
current source are authoritative over reusable examples.

## Development

Use the `mule-development` skill for Mule source changes and complete its post-development checklist.
Preserve contracts, delivery semantics, error outcomes, privacy boundaries, and project conventions.

## Troubleshooting and operations

Use `mule-troubleshooting` for RCA and `mule-ops` for runtime health analysis. Separate observations,
hypotheses, confirmed causes, and unresolved gaps.

## Build

Use the project build workflow or configured Mule build tools. Treat versioning, changelog updates,
tags, deployment, and test skipping as explicit release choices rather than automatic build steps.

## Documentation

Use `document-mulesoft-project` for documentation creation and targeted refreshes.

## Review

Use `review-mulesoft-project` for change, PR, project, and release-readiness reviews. Report findings
and remediation options without changing source or PR state unless explicitly requested.

## Privacy

Do not introduce identity, topology, payloads, endpoints, schedules, volumes, or incident details
from another project. Never expose secrets, tenants, private hosts, personal data, or raw production
payloads.
