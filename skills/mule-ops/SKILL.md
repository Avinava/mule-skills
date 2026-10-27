---
name: mule-ops
description: Assess MuleSoft runtime health across one or more applications from Anypoint logs, metrics, deployment state, audit history, and cross-system correlation, and plan, apply, and watch an authorized release, hotfix, rollback, or change to a running app (version, settings, secrets, runtime, integration identity) without losing or duplicating events. Use for health checks, incident-window evidence, error spikes, deployment-impact checks, release watches and health definitions, hypercare, and recurring operational reviews. Use the configured Anypoint connector, or apply the same evidence workflow to exported telemetry. Route causal root-cause analysis of a specific symptom to mule-troubleshooting, source changes to mule-development, and local packaging to mule-build.
---

# Mule Operations Analysis

Produce an evidence-backed operational assessment across the applications that participate in a
request, event, scheduler, or batch path. Treat application roles as discovered facts rather than
assuming every project uses a Process API and System API pair.

## Privacy and reuse boundary

- Treat logs, audit records, configuration, payloads, correlation identifiers, application names,
  organization details, user names, and endpoints as potentially sensitive.
- Use actual identifiers only when required to query the authorized environment. Do not copy them
  into this reusable skill, examples, unrelated reports, or future project guidance.
- Never include secrets, tokens, raw payloads, personal data, tenant identifiers, private hostnames,
  or deployer identity in a report. Paraphrase representative messages and redact identifiers.
- Generalize prior incident lessons into diagnostic checks. Never encode a prior client's topology,
  volumes, schedules, retention periods, error counts, or system names as defaults.

## Establish the analysis map

Before collecting telemetry, determine:

1. Requested environment, time window, and reporting timezone.
2. Entry application and all known participating Mule applications.
3. Each application's role, such as entry API, orchestration service, system-facing API, worker,
   scheduler, or event consumer.
4. Expected dependency edges and correlation mechanism from repository or deployment evidence.
5. Whether the user wants a single-app check, an end-to-end chain, or an environment-wide review.

Discover these facts from the current repository and authorized Anypoint metadata first. If scope is
still ambiguous, offer concise options and allow the user to skip unknown items. Do not invent a
companion application or an API-led layer.

Use neutral placeholders in examples:

| Placeholder | Meaning |
| --- | --- |
| `<ENTRY_APP>` | Application where the observed path begins |
| `<DEPENDENCY_APP>` | Participating downstream or asynchronous Mule application |
| `<ENV>` | Authorized Anypoint environment |
| `<HOURS>` | Requested lookback window |

## Authorized artifact operations

When the user explicitly requests publication or deployment of a locally built JAR, follow
[Artifact identity handoff](../mule-build/references/artifact-handoff.md) in addition to the Anypoint
readiness gate. Preserve the reviewed digest and embedded identity, disclose any approved coordinate
remap, and keep publication, deployment, and runtime verification outcomes separate. Operational
analysis alone never authorizes a mutation.

For any authorized change to a running app (version, settings or secrets, runtime, authentication
flow or integration user), follow [Safe change](references/safe-change.md): compare the deployed
artifact with the repository first, check the environment boundary and identity dependents, deploy
subscription apps with stop-start rather than rolling, and verify with side-effect-free probes.

For a release, hotfix, rollback, or hypercare period, also follow
[Release lifecycle](references/release-lifecycle.md): record what runs and the rollback plan
first, watch at fixed checkpoints, call the release healthy only on its positive definition, and
tag only after production proves the release.

## Evidence states

Classify material conclusions:

| State | Meaning |
| --- | --- |
| Observed | Directly present in telemetry or deployment metadata |
| Correlated | Events align by correlation ID or timestamp with adequate coverage |
| Hypothesis | Plausible explanation that still needs a discriminating check |
| Confirmed | Hypothesis supported by the relevant application and dependency evidence |
| Unresolved | Evidence is missing, contradictory, or outside retention |

Never label temporal overlap as causation by itself.

## Workflow

### 0. Confirm Anypoint access

Runtime evidence comes from an authenticated connector, so establish access state before the first
collection call. Follow [Anypoint access readiness](references/anypoint-readiness.md): probe with
`whoami` and `list_environments`, classify the result, and when the state is not `Ready` offer the
user setup, supplied exports, or a repository-only scope with labeled gaps.

Do not use a collection tool as the probe, and do not treat a tool error mid-collection as an
environment finding. Record the resulting access state for the coverage ledger.

### 1. Collect broad signals

For every in-scope application, collect independent telemetry in parallel when the tools support it:

```text
mcp_anypoint-connect_get_log_stats(appName: "<APP>", environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_analyze_errors(appName: "<APP>", environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_get_log_patterns(appName: "<APP>", environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_get_app_status(appName: "<APP>", environment: "<ENV>")
```

Collect environment metrics once, then filter to the in-scope applications:

```text
mcp_anypoint-connect_get_metrics(environment: "<ENV>", hoursBack: <HOURS>, groupBy: "app")
mcp_anypoint-connect_get_metrics(environment: "<ENV>", hoursBack: <HOURS>, groupBy: "worker")
mcp_anypoint-connect_get_runtime_metrics(environment: "<ENV>", hoursBack: <HOURS>)
```

`get_metrics` returns request and failure counts, failure rate, average/min/max and p50–p99 latency
(ms), outbound calls and failures, and message counts per app or per worker. Omit `environment` only
when the question is a cross-environment comparison. `get_runtime_metrics` returns per-worker JVM and
host signals: heap, the old-generation pool and its limit, metaspace, old-generation GC count and time
inside the window, CPU load, and free physical memory. Sizes are bytes, loads are 0–1 fractions, and
durations are milliseconds.

A monitoring tool error means a bad query, a permission gap, or a platform problem; record it as a
coverage gap. An empty result means no traffic was recorded in the window.

Record for each source:

- requested window and actual earliest/latest timestamp
- entry count, unique correlations when available, and log-level distribution
- grouped errors with counts, first/last occurrence, flow, and representative correlation IDs
- request volume, failure rate, average and percentile latency, outbound calls, old-generation
  usage against its limit, GC, CPU, and replica balance
- gaps, truncation, sampling, aggregation interval, and tool errors

Do not compare applications over unequal coverage without narrowing to their overlapping window.

### 2. Add deployment and change context

Query recent application audit activity and current status:

```text
mcp_anypoint-connect_get_audit_log(hoursBack: <AUDIT_WINDOW>, objectTypes: ["Application"], limit: <LIMIT>)
```

Convert epoch timestamps explicitly and report the timezone. Compare deployments, restarts, replica
transitions, and configuration changes with error or latency windows. Treat audit snapshots as
historical state and query current application status before describing present health.

Read the current repository's changelog, commit history, deployment workflow, and version metadata
when available. Match the running artifact version before attributing a behavior to a code change.

### 3. Build a coverage ledger

Create a compact table before drawing conclusions:

| Source | Requested window | Actual coverage | Gaps | Safe comparison window |
| --- | --- | --- | --- | --- |
| Anypoint access | ... | Access state from step 0 | Analysis paths it closed | ... |
| Entry logs | ... | ... | ... | ... |
| Dependency logs | ... | ... | ... | ... |
| Metrics | ... | ... | ... | ... |
| Audit events | ... | ... | ... | ... |

High-volume or verbose logging can shorten accessible history. Verify retention from timestamps;
never assume one application retains less data because of its architectural role.

### 4. Correlate the path

For each dominant or high-severity signature:

1. Identify the earliest observed failing component and time.
2. Trace the same correlation identifier across participating applications when propagation is
   verified. If it is not propagated, correlate by a narrow timestamp, route, and operation while
   lowering confidence.
3. Separate the component that reports an error from the component that originates it.
4. Check response status, connector error, retry wrapper, error-handler outcome, and final caller
   result.
5. Deduplicate multiple log entries from the same transaction before calculating incident counts.
6. Verify whether logs cover the interval and whether relevant failures are logged at ERROR, WARN,
   INFO, or only as structured response fields.

A caller-side 5xx with no dependency ERROR entry does not prove that an external system caused the
failure. Possible explanations include incomplete retention, different log levels, handled errors,
missing correlation propagation, proxy behavior, or an unobserved dependency. List the checks that
would distinguish them.

### 5. Investigate conditional signals

After broad collection, read [references/conditional-signals.md](references/conditional-signals.md)
for the latency, replica imbalance, error burst, memory, CPU and host memory, back pressure, and
warning checks, and for focused log and time-series retrieval. Judge memory by the old-generation
pool, not total heap. Use focused retrieval only after broad collection identifies a reason, and
search with the least sensitive stable term.

### 6. Report the result

Return the analysis in the requested location or directly in the response. Do not create a durable
artifact unless the user asks for one. Read
[references/report-and-lessons.md](references/report-and-lessons.md) for the required report
structure and the reusable diagnostic lessons. State denominators and windows for every rate, present
percentile latency with request count, keep expected business filters separate from technical
failures, and preserve an `Unresolved` state when coverage cannot support attribution.

Interpret recurring mechanisms through `mule-development` Classes A–E and its mandatory cross-cutting
gates. Use source inspection or troubleshooting before turning an operational signal into a code
conclusion. Do not recommend concurrency or pool numbers without measured traffic, replica count, and
dependency capacity for this environment.

## Completion checklist

- Confirm the access state and, when it was not `Ready`, what the assessment could not establish.
- Confirm every in-scope source's actual coverage.
- Confirm counts represent unique transactions or clearly label raw log-entry counts.
- Separate observations, hypotheses, confirmed causes, and recommendations.
- Confirm current state after any deployment-window finding.
- Flag repeating identical errors for disposition investigation (permanent/poison vs intentional retry).
- Check applicable cross-cutting security/configuration, capacity/lifecycle, delivery/transaction,
  privacy/observability, and validation evidence before recommending a durable change.
- Match logged app version to packaged artifact when version metadata exists.
- Remove secrets, payloads, identities, private endpoints, and raw correlation identifiers.
- State what was not checked and why.

## Gotchas

- A monitoring tool error is a coverage gap (bad query, permission, or platform problem); an empty
  result means no traffic was recorded in the window.
- A total-heap sawtooth is normal collection activity. Judge pressure by the old-generation pool.
- Audit timestamps are epoch values. Convert them explicitly and state the timezone before comparing
  with error windows.
- A deployment overlapping an error spike is a hypothesis, not a cause, until lifecycle messages or
  before and after behavior support it.
- A deployed artifact can differ from the repository. Compare them before attributing behavior to
  a commit or changing the app.
- Classify connector log lines against the `mule-connectors` profile's known signatures before
  counting them as errors.
- Do not use a collection tool as the readiness probe, and do not treat a mid-collection tool error
  as an environment finding.
- Platform properties override packaged files. Read the effective settings before reasoning from
  the repository's property files.
- Every start loses something, including a platform patch nobody requested. Classify unexplained
  restarts with the audit log and run the post-start checks for them too.
