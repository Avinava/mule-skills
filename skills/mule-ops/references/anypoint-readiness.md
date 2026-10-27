# Anypoint access readiness

`anypoint-connect` is the only MCP server in this toolkit that needs authentication. Establish the
requested capability rather than assuming that one successful call proves access to every Anypoint
service. A failed collection call cannot tell missing access apart from an empty result.

This reference is owned by `mule-ops` and shared with `mule-api-design`, `mule-troubleshooting`,
`mule-review`, and `mule-build`. Read it from
`<skills-root>/mule-ops/references/anypoint-readiness.md`.

## Contents

1. [When to probe](#when-to-probe)
2. [Probe sequence](#probe-sequence)
3. [Access states](#access-states)
4. [Offer the user a choice](#offer-the-user-a-choice)
5. [Guided setup](#guided-setup)
6. [Working from user-supplied evidence](#working-from-user-supplied-evidence)
7. [Evidence labeling](#evidence-labeling)
8. [Consent and privacy](#consent-and-privacy)
9. [Report the access state](#report-the-access-state)

## When to probe

Probe once per session, before the first `anypoint-connect` call, and again after a setup step or an
environment change.

| Work | Probe first |
| --- | --- |
| Runtime health, incident telemetry, deployment or audit history, queue, Object Store, or API-manager evidence | Yes |
| Design Center, Exchange, centralized API Governance, or API publication | Yes, using the design capability probe |
| Explicitly requested publish, deploy, rollback, restart, scale, or settings change | Yes |
| Repository-only analysis, documentation, development, lint, local validation, test, or packaging | No |

Do not probe to satisfy curiosity. If the requested work needs no runtime evidence, skip this
workflow entirely rather than raising a setup question the user did not need.

## Probe sequence

Cheapest sufficient call first, and stop as soon as the state is established:

```text
mcp_anypoint-connect_whoami()
mcp_anypoint-connect_list_environments()
```

`whoami` confirms authentication and organization context. Select the second probe by capability:

| Capability | Second probe | Ready means |
| --- | --- | --- |
| Runtime/deployment/telemetry | `mcp_anypoint-connect_list_environments()` | The requested runtime environment is visible |
| Design Center authoring | `list_design_center_projects` | Project inventory is readable, even when empty |
| Exchange discovery | `search_exchange` with a neutral narrow query | Exchange responds within the authorized scope |
| Centralized API Governance | `explain_api_governance_plan` for user-approved neutral coordinates | Governance responds or returns a legitimate empty plan |

Do not call `list_environments` as a prerequisite for Design Center: runtime environment visibility
is unrelated to API design-project access. Call `mcp_anypoint-connect_get_entitlements()` only when
a runtime capability question remains, such as monitoring, queue, or Object Store availability.

Never use a collection tool as the probe. An empty `get_log_stats` result is indistinguishable from
an unauthenticated one, and a permission error on a narrow query says nothing about the rest of the
environment.

## Access states

| State | Signal | What it means |
| --- | --- | --- |
| Ready | `whoami` succeeds and the capability-specific probe succeeds | Use only the proven capability |
| Not configured | The host exposes no `anypoint-connect` tools, or the server is disabled or failed to start | MCP configuration is missing for this host; authentication is not the problem |
| Not authenticated | Tools exist but report missing, invalid, or expired credentials | A login or token refresh is needed |
| Environment not visible | Authentication succeeds but the requested environment is absent from the list | Wrong organization or profile, a business-group boundary, or a misspelled environment |
| Not permitted | Authentication and environment resolve, but an operation is refused or an entitlement is absent | The identity or subscription lacks that capability; a different scope or a different evidence source is needed |
| Transient failure | Timeout, rate limit, or server error that a retry or a narrower window resolves | Retry once with a narrower request before treating it as an access problem |

Distinguish `Not configured` from `Not authenticated` before saying anything to the user. They lead
to different actions, and telling someone to log in when their host never started the server wastes
the exchange.

## Offer the user a choice

On any state other than `Ready`, state the access state in one sentence and offer concise choices.
Follow the toolkit convention: two to four options plus `Other (please specify)` and
`Not sure / Skip`.

```text
Runtime evidence needs Anypoint access, and the connector is not authenticated. How do you want to
proceed?
  A) Set it up now — I will show the commands and you run them
  B) You supply exported logs or metrics for the window and I analyze those
  C) Continue with repository-only analysis and I label the runtime gaps
  D) Other (please specify)
  E) Not sure / Skip
```

Ask once. If the user declines, skips, or does not answer, continue with the repository-only path,
record the gap in the coverage section of the report, and do not raise the question again in the
same session.

Never present setup as mandatory when the requested work has a useful degraded form. Review,
troubleshooting, and documentation all produce defensible output without runtime access as long as
the missing coverage is visible in the result.

## Guided setup

Print the commands and let the user run them. These change machine-local state, so do not run them
without explicit approval.

The current connector requires Node.js 22 or newer and a user Authorization Code login. Its
Connected App requests `full offline_access`; Client ID and Secret alone are not supported headless
CI authentication. Never ask the user to reveal either value. `config init` masks the secret, and
the detailed administrator setup belongs to
<https://avinava.github.io/anypoint-connect/credentials/>.

```bash
npx -y @sfdxy/anypoint-connect@0.17.0 config init
npx -y @sfdxy/anypoint-connect@0.17.0 auth login
npx -y @sfdxy/anypoint-connect@0.17.0 auth status
```

A global install gives the shorter `anc` form and needs separate approval:

```bash
npm install -g @sfdxy/anypoint-connect@0.17.0
anc auth login
anc auth status
```

With more than one organization, use a neutral local profile identifier rather than an organization
or customer name:

```bash
anc config init --profile org-a
anc auth login --profile org-a
anc config use org-a
```

`anc config use` writes `.anypoint-connect.json` and changes the machine-local default profile for
the whole project, so treat it as a separate approval and suggest adding the file to `.gitignore`.

For `Not configured`, the fix is host MCP configuration rather than login. Point the user at the
install documentation for their host and, where the host supports it, the command that lists MCP
servers. After any setup step, re-run the probe before collecting anything.

## Working from user-supplied evidence

When the user chooses to supply evidence, ask for the narrowest artifacts that answer the actual
question, and ask for their metadata in the same message.

| Gap | Ask for | Required metadata |
| --- | --- | --- |
| Error and log signals | Downloaded application log for the window, or an error-grouping export | Application, environment, window with timezone, log level, whether the export was truncated |
| Latency and throughput | Monitoring dashboard export or screenshots covering the window | Aggregation interval, request count behind each percentile, replica scope |
| Memory and garbage collection | Memory or heap chart export for the window | Interval, replica identity or count, axis units |
| Deployment and change context | Deployment history view or release notes | Timestamps with timezone, artifact version, replica or worker changes |
| Current health | Current application status view | Time the snapshot was taken, desired versus current state |

Also state what you will not be able to conclude from exports alone: correlation across
applications when identifiers are absent, coverage beyond the exported window, and anything the
export's log level never recorded.

Treat supplied files as sensitive. Read them from a path the user names, do not copy them into the
repository, do not commit them, and quote only paraphrased or redacted lines in the result.

## Evidence labeling

| Source | Enters as | Can support |
| --- | --- | --- |
| Authorized connector query | Observed | Correlated and Confirmed conclusions within stated coverage |
| User-supplied export with full metadata | Provided | Correlated conclusions when window and completeness are stated |
| User-supplied export without metadata | Provided, coverage unknown | Hypotheses only |
| User's verbal description of a symptom | Provided | Scope and timeline, not a mechanism |

A user-supplied export never becomes `Observed` because it was convenient, and absence of an entry
in an export is not evidence of absence: the export may have been truncated, filtered, or written
at a level that never captured the event. Keep these labels consistent with the evidence-state table
in the calling skill, and keep the distinction visible in the report rather than in your reasoning
only.

## Consent and privacy

- Never run an install, login, logout, or profile-switch command without explicit approval. Print it
  instead.
- Never run a mutating Anypoint operation — deploy, rollback, restart, scale, delete, settings, or
  queue publish — as part of establishing readiness.
- By default, the mutating tools ask for approval on every call: `deploy_app`, `deploy_jar`,
  `update_app`, `update_app_artifact`, `update_app_settings`, `restart_app`, `rollback_app`,
  `scale_app`, `start_app`, `stop_app`, `delete_app`, `publish_app_jar` and `smoke_test_api`.
  A property write is a full redeploy, so settings tools count. A user may pre-approve some or all
  of them in the host's permission settings, for example for sandbox automation. Respect that
  choice: pre-approval removes the host prompt, not the workflow. Still preview first and name the
  exact app and environment before the commit call.
- Production needs its own confirmation. By default, ask the user in the conversation before
  sending `confirmProduction: true`. A user can pre-approve production with
  `set_production_preapproval`, which stores the approval outside the repository, bound to the
  organization and environment IDs, for named tools and an optional expiry. When the preview reports
  `productionPreapproved: true`, proceed without asking again, but state in the reply that the
  pre-approval applied, which environment and tool it covered, and its expiry. A
  `preapprovalWarning` means an approval found in a project file was ignored; ask as usual. Pre-approval
  never waives the preview, the bound identifiers, or the artifact checks below.
- Production artifact checks: every production change that selects an artifact verifies the build
  marker of the jar it will run, downloaded from Exchange when no local jar is given. A stripped,
  inconsistent or unknown marker is refused. A jar with no marker (built by another pipeline, or
  before mule-build 3.2) is refused unless the user allowed unmarked artifacts for that environment
  with `set_unmarked_artifact_allowance`. Check the rollback target before a release; if it is
  unmarked, the rollback needs that allowance, so settle it while the release is planned, not during
  an incident.
- Never suggest, create, widen, or extend a pre-approval or allowance yourself, and never change host
  permission settings. Set one only when the user explicitly asks, through the tool's preview and
  `confirm: true`. The project documentation on Anypoint access shows each setup.
- Never echo the organization name, organization identifier, user name, email address, or profile
  identifier into a report. Say `the authorized environment` and name the environment only by the
  label the user used.
- Do not report which profile is active or that multiple organizations exist. That is local
  configuration detail, not evidence.
- Do not persist telemetry, exports, or credentials anywhere in the repository.
- Ask once per session. A declined offer is an answer, and repeating it is noise.

## Report the access state

Every report whose scope was affected records the access state, so the reader can tell a clean
result from an unexamined one. Add a row to the coverage ledger:

| Source | Requested window | Actual coverage | Gaps | Safe comparison window |
| --- | --- | --- | --- | --- |
| Anypoint access | ... | `Ready`, `Not configured`, `Not authenticated`, `Environment not visible`, `Not permitted`, or `Transient failure` | Analysis paths this closed | ... |

When the state is not `Ready`, also state in one sentence what would change in the conclusion if
runtime evidence became available. That is the difference between an honest gap and a hidden one.
