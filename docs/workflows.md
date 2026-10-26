# Workflow examples

The skills compose around a task. You describe the desired Mule outcome; the agent selects the
smallest useful workflow and adds another skill only when the task crosses a real ownership boundary.
For captured results from pinned sample projects, including a blocked MUnit gate, see
[Mule Skills in action](see-it-in-action.md). This page focuses on reusable workflow shapes.

## Design and implement an API change

```text
Design a GET /orders/{orderId} operation for the existing Orders System API. Reuse the repository's
RAML conventions, record unresolved consumer decisions, validate the contract, and stop before
implementing it.
```

Expected path:

```mermaid
flowchart LR
    Evidence[Existing RAML/OAS and project context] --> Design[mule-api-design]
    Design --> Contract[Validated contract + decision ledger]
    Contract -->|after approval| Development[mule-development]
    Development --> Tests[mule-testing]
    Tests --> Gate[mule-build + mule-lint]
```

The design skill does not claim that APIKit implementation or Design Center publication happened.
Those are later, separately evidenced steps.

## Implement and test Mule behavior

```text
Implement the approved order lookup behavior. Preserve the current error contract, add focused MUnit
coverage, refresh only documentation made stale, and review the resulting change.
```

The agent should:

1. read repository instructions and current Mule/runtime/connector versions;
2. implement production XML or DataWeave through `mule-development`;
3. author behavior-faithful tests through `mule-testing`;
4. run focused and required full validation through `mule-build` and `mule-lint`;
5. refresh affected documentation and return a read-only review.

An implementation request authorizes source changes inside that scope. It does not authorize a
commit, push, version bump, runtime change, or deployment.

## Check and upgrade dependencies

```text
Which connectors in this project are outdated, and what is the newest release that fits our Mule
runtime and Java version? Do not change the pom yet.
```

`mule-dependencies` reads the project's runtime and Java constraints, looks up each dependency
through the Exchange asset API (falling back to the Exchange Maven facade and the MuleSoft releases
repository, never Maven Central), and reports the newest and newest compatible release with the
source and fetch time. If the network is unavailable it says so and uses the dated offline
snapshot, labelled unverified. Applying the upgrade is a separate `mule-development` step, verified
through `mule-build`.

## Switch a connector's authentication safely

```text
Move our Salesforce connection from username and password to OAuth client credentials. Tell me what
has to change, then deploy it to the sandbox and prove it works without writing test data.
```

`mule-connectors` checks the project's connector version against the profile and live release
notes (`mule_versions.py notes`), because a connection type can be missing in an older major and
removed in a newer one. It names the token URL rule, where the run-as user is configured, and how to
prove the identity afterwards. `mule-development` makes the configuration change with one secret
supply model per key: `${key}` for a platform secure property, `${secure::key}` only for an encrypted
file. `mule-ops` then follows its safe-change playbook: compare the deployed artifact with the
repository, check what depends on the integration user, deploy subscription apps with stop-start
instead of a rolling update, supply the secret from a file without echoing it, and verify with a
probe that stops at a guard rather than writing a record.

## Validate and package

```text
Validate and package this Mule application. Run the established security, lint, and MUnit gates and
report the exact artifact. Do not skip tests or perform release actions.
```

`mule-build` uses repository commands first and the pinned `mule-build@3.1.0` tool when configured.
The normal sequence is read-only readiness, static/security checks, MUnit, package, then artifact
verification. A package result should make these visible. This is a handoff template, not captured
output from a bundled sample:

```text
Mode: package
Validation: <passed, failed, or blocked with the exact gate>
MUnit: <run, failed, errors, and skipped totals>
Artifact: <exact path, or none when packaging failed>
Changed by workflow: target/ only
Release actions: none
```

## Prepare, publish, and deploy a release

This is deliberately two ownership zones:

```mermaid
flowchart LR
    Local[mule-build<br/>check, test, package] --> Review[mule-review<br/>release readiness]
    Review --> Version[mule-build<br/>version, commit, tag]
    Version --> Boundary{Separate approval}
    Boundary --> Publish[anypoint-connect<br/>Exchange publish]
    Boundary --> Deploy[mule-ops + anypoint-connect<br/>runtime deployment]
```

A request to “prepare a release” stops with a versioned/tagged local candidate unless the user also
explicitly requests and approves the Anypoint action. A successful artifact is never treated as
deployment approval.

## Diagnose an incident

```text
Find the cause of the order API timeout increase between 09:00 and 10:00 UTC. Use authorized runtime
evidence if available; otherwise tell me which exports you need. Diagnose only—do not change source,
configuration, or runtime state.
```

`mule-troubleshooting` traces the symptom through code, configuration, dependencies, logs, metrics,
and change windows. `mule-ops` gathers authorized runtime evidence. If access is missing, the result
labels the coverage gap and offers setup, supplied exports, or repository-only analysis.

## Refresh project documentation

```text
Refresh onboarding, architecture, and operations documentation for this Mule project. Use source and
committed configuration as evidence, label inferred business purpose, and never expose secret values
or private endpoints.
```

`mule-docs` inventories the current repository and creates only evidenced pages. It can show flow and
dependency relationships with Mermaid, while keeping missing ownership or operational facts visible
instead of inventing them.

## Review before asking for fixes

```text
Review the current branch for Mule correctness, contract drift, MUnit gaps, configuration safety,
and release readiness. Report prioritized findings and fix options; do not modify files or PR state.
```

Review is read-only. After you accept a finding, ask `mule-development`, `mule-testing`, or
`mule-build` to implement the specific fix and rerun the affected gate.
