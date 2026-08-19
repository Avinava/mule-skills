---
name: mule-build
description: Validate, test, and package a MuleSoft Mule 4 application using its established repository commands and configured build tools, and perform release actions only when the user explicitly requests them. Use for build, validation, static analysis, MUnit test runs, packaging a deployable artifact, and release preparation covering version bumps, changelog entries, tags, publishing, and deployment. Default to validate-and-package; treat versioning, publishing, deploying, pushing, and skipping tests as explicit user choices rather than automatic build steps.
---

# Build Mule Application

Build the current Mule 4 application using its repository instructions and configured build tools.
Default to a validation and package operation. Do not turn a build request into a release.

This skill owns test execution, reports, packaging, and release mechanics. Route MUnit authoring,
repair, fixtures, mocks, and assertions to `mule-testing` when that skill is installed.

## 1. Establish scope

Distinguish these modes:

| Mode | Actions |
| --- | --- |
| Validate | Static checks and tests only |
| Package | Validate, test, and create a deployable artifact |
| Release | Explicit version, changelog, tag, and optional publish/deploy workflow |

If the user says only `build`, use **Package**. Version bumps, changelog edits, commits, tags,
publishing, deployment, and pushing require explicit user scope.

## 2. Inspect before changing anything

1. Read repository instructions, `pom.xml`, `mule-artifact.json`, build scripts, CI workflows, and
   relevant changelog or release policy.
2. Review `git status --short` and preserve unrelated or uncommitted changes.
3. Confirm required Java, Maven, Mule runtime, and connector versions.
4. Identify the project's established validation, test, package, and release commands.
5. Check whether the requested build needs network or authenticated artifact repositories.

Do not copy organization names, application identity, repositories, profiles, endpoints, or
credentials into reusable commands or output.

## 3. Validate the source

Before choosing a lint profile, follow the shared
[mule-lint standards protocol](../mule-development/references/mule-lint-standards.md). The build
workflow executes the project gate; it does not redefine which Mule practices or rules are canonical.

Run the project's configured checks before packaging. Prefer, when available:

1. XML, DataWeave, RAML/OAS, and configuration validation;
2. Mule lint and security checks;
3. focused MUnit tests for changed behavior;
4. the required full test suite.

Do not skip tests by default. Skip them only when the user requests it or the repository's documented
workflow requires a separate test stage, and state the resulting verification gap.

When Mule source changed, use the `mule-development` post-development checklist before building.
When Mule XML changed and the development skill is installed, run:

```bash
python3 <skills-root>/mule-development/scripts/check_embedded_expressions.py .
```

`<skills-root>` is the directory holding the `mule-*` skills: `${CLAUDE_PLUGIN_ROOT}/skills` when
installed as a Claude Code plugin, `.agents/skills` when vendored into the project.

This catches truncated `#[…]` expressions in CDATA that XML parsing and packaging can miss.

## 4. Reconcile contracts and documentation

Review the changed files and update only documentation made stale by the change:

| Change | Check |
| --- | --- |
| Endpoint, event, or payload | API/event contract and consumer guidance |
| Flow, route, or dependency | Architecture and flow documentation |
| Scheduler, batch, queue, retry, timeout, or concurrency | Operations guidance |
| Configuration key or deployment input | Onboarding and configuration tables |
| Error mapping or recovery behavior | Contract, troubleshooting, and runbook |
| Test or validation command | Contributor/build guidance |

Use the `mule-docs` targeted-refresh workflow when installed. Do not rewrite
unrelated prose or add unsupported business context.

## 5. Package

Use the repository's established command or the configured Mule build tool. For a tool call, pass the
project root as `cwd` and preserve the project's normal test behavior.

Before running, show or record:

- command or tool and relevant non-secret options;
- whether tests are enabled;
- expected artifact directory;
- any known network or authentication dependency.

If the build fails, report the first actionable failure and relevant context. Do not mask a failed
test by rerunning with tests skipped unless the user approves that diagnostic step.

## 6. Release actions, only when requested

When the user explicitly requests a release:

1. Apply the repository's versioning policy. If none exists, propose patch, minor, or major with the
   compatibility rationale and obtain direction when the choice is material.
2. Update all evidenced version surfaces that must remain synchronized.
3. Update an existing changelog using its established format; do not create one unless requested or
   required by repository instructions.
4. Re-run validation, tests, and packaging after version changes.
5. Use `mule-review` in release-readiness mode on the resulting candidate when the skill
   is installed. Do not continue on `Not ready` or `Unresolved`; complete or explicitly accept every
   condition before continuing from `Ready with conditions`.
6. Commit or tag only when authorized. Make an annotated tag only after the final release commit.
7. Push, publish, or deploy only when explicitly requested.

Publishing to Exchange and deploying, restarting, scaling, or rolling back a runtime go through the
authenticated Anypoint connector. Validation, testing, and packaging do not. Before an authorized
publish or deploy, confirm access with `<skills-root>/mule-ops/references/anypoint-readiness.md` and
stop on any state other than `Ready` — report the state and the setup step instead of retrying the
operation. Never treat a readiness probe as approval to deploy.

Use semantic-version guidance as a starting point, not a replacement for the project's release
policy:

| Change | Typical bump |
| --- | --- |
| Backward-compatible fix | Patch |
| Backward-compatible capability | Minor |
| Breaking public contract or runtime compatibility | Major |

Configuration-only changes do not universally mean “no version bump”; follow how the project
packages and deploys configuration.

## 7. Verify the artifact

After a successful package:

- locate the generated deployable artifact;
- confirm it was produced by the current build and is not a stale file;
- confirm the packaged version matches the intended build or release version;
- report whether tests, lint, and security checks passed, failed, or were skipped;
- confirm no secret-bearing configuration or unintended generated files entered the diff.

## 8. Report

Provide:

1. build mode and outcome;
2. exact artifact path;
3. validations and tests run;
4. tests or checks skipped and why;
5. files changed by the workflow;
6. version, commit, and tag only when release actions occurred;
7. remaining warnings or user actions.
