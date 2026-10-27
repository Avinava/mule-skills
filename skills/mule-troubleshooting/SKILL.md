---
name: mule-troubleshooting
description: Diagnose MuleSoft incidents and produce evidence-backed root-cause assessments or fix plans for timeouts, connection failures, rate limits, concurrency, batch processing, queues, deployment transitions, platform-initiated restarts, lost or delayed events, memory pressure, and cross-application error propagation. Use when a specific Mule runtime symptom must be traced to its cause through code, configuration, logs, metrics, and dependencies. Diagnose by default; modify source or configuration only when the user explicitly requests implementation. Route broad health checks, release watches, and authorized runtime changes to mule-ops, and connector behavior questions to mule-connectors.
---

# MuleSoft Troubleshooting and RCA

Trace symptoms across the complete execution path, distinguish the reporting component from the
originating component, and require a discriminating check before calling a hypothesis the root
cause.

## Privacy and reuse boundary

- Treat repositories, logs, payloads, application names, endpoints, organization metadata,
  correlation identifiers, and audit users as sensitive.
- Use role labels such as `Entry API`, `Orchestrator`, `System-facing API`, `Queue`, and `Target
  System` in reusable examples.
- Never transfer names, identifiers, sample payloads, exact schedules, traffic volumes, error
  counts, or topology from a prior project into this skill or another project.
- Use actual project identity only when necessary inside the authorized investigation, and keep it
  out of reusable findings.

## Investigation contract

Before analysis, establish:

- symptom, user impact, first-known time, environment, and timezone
- affected request, event, scheduler, batch job, or queue path
- participating applications and external dependencies
- recent deployments or configuration changes
- whether the user wants diagnosis only, a fix plan, or implementation

If the user cannot provide a fact, continue with available evidence and label the gap. Do not ask
for information that repository or authorized runtime evidence can answer.

Use these confidence states:

| State | Meaning |
| --- | --- |
| Observed | Directly present in code, configuration, logs, or metrics |
| Correlated | Aligned by correlation ID or time with adequate coverage |
| Hypothesis | Plausible cause awaiting a discriminating check |
| Confirmed | Supported across the components needed to rule out alternatives |
| Unresolved | Evidence is missing or contradictory |

## Phase 1: Build the evidence set

### 1. Map the real execution path

Read the relevant Mule XML, referenced flows, DataWeave, connector configurations, property keys,
error handlers, API contract, MUnit tests, deployment files, and current documentation. Follow:

- synchronous calls and their response path
- asynchronous publishes, acknowledgements, and consumers
- retry, reconnection, and fallback scopes
- scatter-gather, parallel-for-each, batch, and queue boundaries
- local and global error handlers

Do not infer API-led layers or dependency ownership from application names alone.

When an isolated reproduction or failing MUnit suite is material, use `mule-testing` to inventory
and classify the test evidence. A correct failing test can support a product hypothesis; a mock
mismatch, unfaithful event, or build failure cannot. Keep diagnosis read-only unless the user also
requests implementation.

### 2. Collect aligned telemetry

Confirm Anypoint access before the first connector call, following
`<skills-root>/mule-ops/references/anypoint-readiness.md`. When access is not `Ready`, offer setup,
supplied exports, or a source-only diagnosis, then continue on the chosen path rather than retrying
collection tools.

Use the `mule-ops` collection workflow when available. Otherwise obtain logs and metrics for every
participating Mule application and the narrowest useful time window. Record actual coverage before
comparing sources.

Prefer enough history to include baseline behavior and multiple occurrences, but do not silently
default to a fixed duration when retention or incident timing suggests another window.

When the user supplies the evidence instead, request the artifacts the readiness reference lists —
log export, error grouping, latency or memory charts, deployment history — with the application,
environment, window, timezone, log level, and any truncation stated. Mark them as user-provided.
They reach `Correlated` only when window and completeness are known, and absence of an entry in an
export is not evidence of absence, so it cannot confirm a cause.

### 3. Identify primary signatures

Group by unique transaction and distinguish:

- originating connector or business error
- timeout or connection exception observed by a caller
- retry or reconnection summary
- error-handler and default exception-listener duplicates
- final response, acknowledgement, retry, dead-letter, or continuation outcome

Use correlation IDs where propagation is verified. If they are absent, use narrow time, route, and
operation matching and reduce confidence.

### 4. Build a timeline

For each affected path, order:

1. trigger received
2. key processing stages
3. dependency request started
4. dependency response or failure
5. retry or fallback
6. error mapping
7. caller response or asynchronous disposition
8. deployment or infrastructure events nearby

This timeline prevents a later summary log or upstream timeout from being mistaken for the first
failure.

## Phase 2: Test hypotheses

Discriminate between candidate causes with checks that could prove a hypothesis wrong. Load the
reference that matches the symptom:

- Read [references/hypothesis-checks.md](references/hypothesis-checks.md) for timeouts and
  connection failures (inventory each distinct timer), concurrency and rate limits (estimate
  effective concurrency across the whole path, never recommend a numeric value without observed
  workload), and error propagation through intermediate applications or proxies.
- Read [references/signatures-and-pressure.md](references/signatures-and-pressure.md) for recurring
  mechanism signatures mapped to `mule-development` Classes A–E and the cross-cutting gates, for
  deploy-related bursts, and for memory pressure judged by the old-generation pool.
- Read [references/jvm-diagnostics.md](references/jvm-diagnostics.md) when requests wait or a
  replica looks saturated: read-only checks first, thread-dump reading by pool, blocked cpu-light
  patterns, heap histograms, connection-pool exhaustion signatures, and 502/503/504 attribution,
  including what a managed platform without a shell can and cannot provide.
- Read [references/deployment-failure-triage.md](references/deployment-failure-triage.md) when a
  deployment never reaches running, a replica restarts repeatedly, or an app starts and then fails:
  pod and replica failure signals, out-of-memory termination vs application error, a cause
  checklist, and decoded startup error messages.

A caller-side 5xx or timeout does not identify the origin, and timestamps alone do not prove a
deployment cause. Keep the cause unresolved until a discriminating check separates the alternatives.

## Phase 3: Produce the RCA or plan

Lead with the impact and highest-confidence conclusion. Include:

1. symptom and affected path
2. evidence coverage and gaps
3. timeline of the failure chain
4. hypotheses considered and discriminating evidence
5. confirmed or best-supported cause with confidence
6. contributing conditions
7. immediate containment options
8. durable fix options with tradeoffs
9. rollback and verification plan

For a fix plan, cite exact repository-relative flows, configuration keys, and tests to change. Keep
recommendations separate from current behavior. Do not implement the plan unless requested.

Use Mermaid only when the multi-component sequence or before/after concurrency design is materially
clearer than prose. Keep node labels role-based and free of project identity.

## Phase 4: Verify a fix

Verify against the failure mechanism, not only deployment success:

1. Confirm the intended version and configuration are running.
2. Exercise the affected path under a representative workload.
3. Observe at least one relevant scheduler, batch, queue, or retry cycle when applicable.
4. Compare equivalent pre-change and post-change windows.
5. Confirm the primary signature is absent or reduced at the unique-transaction level.
6. Confirm latency, throughput, memory, and dependency pressure did not regress.
7. Scan for new errors, back pressure, duplicates, loss, or retry amplification.

If the event has not recurred or telemetry coverage is inadequate, report the result as provisional.

## Completion checklist

- Trace all participating components and error handlers.
- Record actual telemetry coverage, timezone, and the Anypoint access state when it limited scope.
- Deduplicate multiple entries from the same transaction.
- Distinguish the first failure from downstream symptoms and retry summaries.
- Calculate the full timeout and concurrency budget before recommending values.
- Treat deploy overlap, missing logs, and sawtooth memory as signals rather than proof.
- Preserve client confidentiality and keep prior-project identity out of reusable examples and
  current-project output.
- State unresolved alternatives and the next discriminating check.

## Gotchas

- A caller-side 5xx or timeout does not identify the origin. Inspect the intermediate application's
  result and error handler before naming a cause.
- Do not apply a universal `idleTimeout >= responseTimeout` rule. Inventory each distinct timer and the
  full retry budget instead.
- A total-heap sawtooth is normal collection activity. A rising old-generation floor is only a leak
  hypothesis until retention evidence supports it.
- Deployment overlap, missing logs, and retry summaries are signals, not proof. A retry-exhaustion
  entry is often secondary evidence.
- Never claim a swallowed error will be reprocessed unless queue and source semantics prove it.
- Connector log lines can be benign by design, such as a periodic subscription reconnect. Check the
  `mule-connectors` profile's known signatures and their criteria before counting them as errors.
- Never raise a connector-internal logger to DEBUG or TRACE in a shared environment without checking
  the profile's sensitive loggers; some write session identifiers or tokens.
