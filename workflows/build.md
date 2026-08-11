---
description: Build the Mule application JAR for deployment
---

# Build Mule JAR

Build the Mule 4 application using the mule-build MCP server.

// turbo-all

## 1. Determine Version Bump

Before building, review the uncommitted or recent changes and decide whether a version bump is needed using semver (`MAJOR.MINOR.PATCH`):

| Change Type | Bump | Examples |
|---|---|---|
| Bug fixes, SOQL field additions, config changes, comment updates, log improvements | **PATCH** | Fix null query params, expand SOQL fields, update timeout values |
| New flows, new integrations, new scheduler, new sub-flows, new DWL modules | **MINOR** | Add transaction sync, new entity termination flow |
| Breaking API contract changes, removed flows, restructured payloads, connector upgrades | **MAJOR** | Change SAPI endpoint paths, drop support for a sync direction |

**Guidelines:**
- If only properties/config changed (yaml files only): **no bump needed** (config is deployed separately via CloudHub properties)
- If any XML flow file changed: **bump at least PATCH**
- If a new flow file was added: **bump MINOR**
- When in doubt, bump **PATCH**

If a bump is needed, use the `mule-build release_version` tool:
- `bump`: `patch`, `minor`, or `major`
- `cwd`: project root directory
- `noPush`: `true` (push manually after verifying)
- `noTag`: `false`

## 2. Update CHANGELOG.md

Maintain a `CHANGELOG.md` in the project root following [Keep a Changelog](https://keepachangelog.com/) format.

**Format:**
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-03-20

### Added
- New user management flows for deferred user creation

### Changed
- Expanded batch SOQL to include additional fields

### Fixed
- Resolved 405 Method Not Allowed for upsert (POST → PATCH)
- Removed hardcoded null query params from update requests

### Removed
- Deprecated legacy restlet endpoint

## [1.1.1] - 2026-03-15
...
```

**Rules:**
- Group changes under: `Added`, `Changed`, `Fixed`, `Deprecated`, `Removed`, `Security`
- Only include sections that have entries (omit empty sections)
- Each entry should be a single concise line describing the user-facing impact
- Reference the Salesforce object or flow name when relevant
- Most recent version goes at the top
- Date format: `YYYY-MM-DD`
- Keep an `[Unreleased]` section at the top for changes not yet deployed

## 3. Tag the Release

After committing all changes (version bump, CHANGELOG, flow changes), create an annotated git tag:

```bash
git tag -a v<VERSION> -m "v<VERSION>: <brief description of changes>"
```

**Rules:**
- Tag format: `v` prefix + semver (e.g., `v1.2.0`)
- Only tag after the commit is made — the tag must point to the final commit
- If the `mule-build release_version` tool was used with `noTag: false`, the tag is already created — skip this step
- Use `git tag -l` to verify the tag was created

## 4. Update Documentation

Review the changes made in this session and check whether any project documentation needs updating to stay aligned. Scan for relevant docs by checking:

| If you changed... | Update these docs |
|---|---|
| Scheduler frequency, batch sizes, concurrency | Operations docs (Performance Tuning tables) |
| External API flows, OAuth, entity management | Integration docs |
| New flows, removed flows, renamed flows | `AGENTS.md` (Key Integration Flows tables) |
| Config properties (yaml keys) | `AGENTS.md` (Configuration table) |
| New tech debt or resolved tech debt | Tech debt docs |
| New gotchas discovered during development | Post-development checklist |

**How to check:**
1. List the files changed in this session (`git diff --name-only` or review recent edits)
2. For each changed flow/config file, check the table above for matching docs
3. Read the relevant doc sections and update any outdated information (scheduler frequencies, connection limits, flow names, property keys, etc.)
4. If no docs need updating, skip this step

> Only update docs that are **factually outdated** by the changes. Do not rewrite docs for style or add speculative content.

When the `document-mulesoft-project` skill is installed, use its targeted-refresh workflow for the
affected documents. Preserve unrelated prose and run its documentation audit before continuing.

## 5. Sync Application Version

Read the `<version>` from `pom.xml` and update the `json.logger.application.version` value in all environment property files to match (e.g., `prod.yaml`, `dev.yaml`, `local.yaml`).

Find the line containing `version: "..."` under the `json.logger.application` section and replace the value with the pom.xml version.

## 6. Build

Run the mule-build `run_build` tool with the following settings:
- `cwd`: project root directory
- `skipTests`: `true`
- Do NOT set `stripSecure` or `environment`

## 7. Report the JAR Path
Report the build result to the user. You MUST explicitly provide the exact full path to the generated JAR file as part of your final response so the user can easily locate and deploy the artifact.
