---
name: mule-ops
description: Analyze MuleSoft runtime health across one or more applications using Anypoint logs, metrics, deployment state, and cross-system correlation. Use for production or non-production health checks, incident windows, error spikes, latency or memory investigations, deployment-impact checks, and recurring operational reviews. Use the available Anypoint connector when configured, or apply the same evidence workflow to exported telemetry. Do not use for source-code changes unless the user also requests a fix.
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
mcp_anypoint-connect_get_metrics(environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_get_performance_metrics(environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_get_memory_metrics(environment: "<ENV>", hoursBack: <HOURS>)
mcp_anypoint-connect_get_worker_metrics(environment: "<ENV>", hoursBack: <HOURS>)
```

Record for each source:

- requested window and actual earliest/latest timestamp
- entry count, unique correlations when available, and log-level distribution
- grouped errors with counts, first/last occurrence, flow, and representative correlation IDs
- request volume, average and percentile latency, outbound calls, memory, GC, and replica balance
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

- **Latency:** Pull time series for the affected app and compare latency with traffic, outbound
  duration, CPU, memory, GC, and replica balance.
- **Error bursts:** Compare the burst with schedulers, batch instances, queue depth, retries,
  dependency limits, and deployments.
- **Memory:** Look for sustained baseline growth after GC, allocation spikes, full-GC pressure, or
  a single replica diverging from peers. A sawtooth alone is normal and not proof of a leak.
- **Back pressure or rate limits:** Estimate effective concurrency from flow limits, source
  consumers, batch-job concurrency, parallel scopes, replicas, and dependency quotas.
- **Warnings:** Sample by pattern and verify recovery or impact. Do not declare a reconnect,
  recursive-flow warning, ignored body, or cache miss harmless without checking the actual outcome.

Use focused retrieval only after broad collection identifies a reason:

```text
mcp_anypoint-connect_get_logs(appName: "<APP>", environment: "<ENV>", search: "<SAFE_TERM>", lines: <LIMIT>)
mcp_anypoint-connect_get_metrics_timeseries(environment: "<ENV>", appName: "<APP>", hoursBack: <HOURS>, granularity: "5m")
mcp_anypoint-connect_get_memory_timeseries(environment: "<ENV>", appName: "<APP>", hoursBack: <HOURS>, granularity: "5m")
```

Search with the least sensitive stable term that identifies the flow or operation. Do not expose
raw results when a count and sanitized pattern are sufficient.

### 6. Report the result

Return the analysis in the requested location or directly in the response. Do not create a durable
artifact unless the user asks for one.

Use this structure:

```markdown
# Runtime health analysis

**Window:** <START> to <END> <TIMEZONE>
**Scope:** <ROLE-BASED APPLICATION LIST>

## Assessment
One paragraph with current health, impact, and confidence.

## Coverage
Actual telemetry coverage and material gaps.

## Health signals
Comparable log, error, latency, memory, GC, and replica observations.

## Correlated incidents
Signature, affected path, count of unique transactions, evidence state, and user impact.

## Deployment and change context
Verified overlaps and what remains unproven.

## Actions
Prioritized immediate checks, durable improvements, owner role, and verification signal.

## Unresolved questions
Only questions whose answers would change the assessment.
```

State denominators and windows for every rate. Present percentile latency with request count. Keep
expected business filters separate from technical failures, and preserve an `Unresolved` state when
coverage cannot support attribution.

## Reusable diagnostic lessons

- Interpret recurring mechanisms through `mule-development` Classes A–E and its mandatory
  cross-cutting gates. Use source inspection or troubleshooting before turning an operational signal
  into a code conclusion.
- A retry-exhaustion summary is often secondary evidence; locate the underlying connector or
  business error with the same correlation ID.
- Structured logger and exception-listener entries can describe one failed transaction; deduplicate
  by correlation ID, flow, signature, and time before counting.
- A deployment overlapping an error spike is a hypothesis until lifecycle messages, replica state,
  version changes, or before/after behavior support it.
- Application status and replica state are point-in-time observations. Distinguish desired,
  transitioning, current, and last-successful versions when the API exposes them.
- Percentiles are unstable at low request counts. Always report the sample size.
- Correlation propagation must be verified in source or telemetry. Mule can adopt an inbound
  `X-CORRELATION-ID`, but outbound propagation depends on configuration.
- Default log level, custom error handling, and proxy behavior determine where a failure appears;
  absence from an error-grouping tool is not evidence of absence.
- The same error signature repeating every scheduler or poll cycle may be a dependency outage, a
  permanent/poison record without terminal disposition, or intentional indefinite retry of retryable
  errors. Hand off to troubleshooting Class D checks before assuming a terminal state is missing.
- Logged application version that does not match the packaged artifact makes before/after and
  deploy correlation unreliable—confirm version surfaces before attributing behavior to a release.
- High-volume cache-miss ERROR noise can mean Object Store miss handling treats expected misses as
  exceptional; confirm miss policy before scaling infrastructure.
- Do not recommend concurrency or pool numbers without measured traffic, replica count, and
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
