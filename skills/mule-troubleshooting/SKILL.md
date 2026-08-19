---
name: mule-troubleshooting
description: Diagnose MuleSoft incidents and produce evidence-backed root-cause assessments or fix plans for timeouts, connection failures, rate limits, concurrency, batch processing, queues, deployment transitions, memory pressure, and cross-application error propagation. Use when a Mule runtime symptom must be traced through code, configuration, logs, metrics, and dependencies. Diagnose by default; modify source or configuration only when the user explicitly requests implementation.
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

### Timeout and connection failures

Inventory each distinct timer instead of comparing similarly named properties blindly:

| Timer | What it governs |
| --- | --- |
| Connect timeout | Time allowed to establish a connection |
| Requester response timeout | Time the caller waits for a response |
| Read timeout | Connector-specific wait for inbound data |
| Connection idle timeout | Lifetime of an unused persistent connection |
| Proxy or gateway timeout | Deadline imposed outside the Mule app |
| Retry duration | Attempts, delay, and per-attempt timeout combined |
| Upstream request deadline | Total time available to return a useful result |

For a synchronous chain, verify that inner work, retries, and error mapping can finish with margin
before the upstream deadline. A connection idle timeout is not automatically the request-processing
deadline, so do not apply a universal `idleTimeout >= responseTimeout` rule across unrelated
components.

Discriminate among:

- dependency slowness
- stale pooled connection or remote close
- exhausted connection pool
- caller deadline shorter than valid processing time
- proxy or load-balancer timeout
- CPU, thread, or event-loop starvation
- retry duration exceeding the caller's budget

### Concurrency and rate limits

Estimate effective concurrency across the whole path:

- source consumer count
- flow `maxConcurrency` and connector-specific back pressure
- batch-job `maxConcurrency` and block size
- parallel scopes and asynchronous handoffs
- replica count and queue distribution
- connection-pool limits
- dependency quotas and rate limits

Treat batch block size as a memory and scheduling parameter, not a direct statement that every
record in a block is sent concurrently. Mule processes record blocks in parallel according to batch
concurrency and runtime capacity. Confirm behavior with metrics or a controlled load test before
choosing a limit.

Evaluate multiple remedies where appropriate:

| Option | Benefit | Tradeoff |
| --- | --- | --- |
| Lower flow or batch concurrency | Protects a constrained dependency | Reduces throughput |
| Add bounded retry with jitter | Absorbs transient failures | Extends latency and can amplify load |
| Queue or bulkhead the work | Isolates callers from bursts | Changes delivery and recovery semantics |
| Increase capacity | Preserves throughput | Adds cost and may move the bottleneck |
| Reduce payload or batch size | Lowers memory and call pressure | Increases call or coordination overhead |

Do not recommend a numeric value without observed workload, replica count, and dependency capacity.

### Error propagation and proxy behavior

A caller-side 5xx or timeout does not identify the origin. Inspect the intermediate application's
operation result and error handler. No ERROR-level entry in an intermediate app can mean:

- insufficient log coverage
- failure logged at another level or only in a structured response
- handled or continued error
- transparent proxy behavior
- missing correlation propagation
- failure before or after that application

Keep the cause unresolved until evidence distinguishes these cases.

### Recurring mechanism signatures

Use these signatures only as hypothesis starters. Confirm with code and aligned telemetry. Mechanism
names match `mule-development` Classes A–E; also apply its security/configuration,
capacity/lifecycle, delivery/transactions, privacy/observability, and validation cross-cutting gates.

| Signature | Leading class | Discriminating checks |
| --- | --- | --- |
| After editing HTTP query/header/uri CDATA: Map/MultiMap or "literal expression" transform errors; packaging was green | B — Expression embedding | Confirm CDATA still ends with `]` before `]]>`; compare the edited block only, not siblings |
| Flow exists in source but an APIKit caller gets 404 / not-found | C — Contract authority | Path absent from **bound** contract → 404; bound path wrong method → 405; bound path without implementation → usually `NOT_IMPLEMENTED`/501; check other sources/callers before calling the flow dead |
| Bound contract route exists but returns not-implemented / 501 | C — Contract authority | Implement or remove the resource/method; check FlowFinder "no implementation" warnings |
| Bound path exists but method fails with 405 | C — Contract authority | Add method to contract and flow, or stop calling the unsupported method |
| `Unable to infer output media type` on vars, `targetValue`, or mixed input expression | A — Value contracts | Make output explicit for the next consumer when inputs differ or inference mismatches it |
| Records never process; logs show skip only; little or no durable error | A or D | Empty vs null ids, dual accessors, known request id; skip path durable signal |
| Same business record fails every scheduler cycle for a long window | D — Failure disposition | Classify permanent vs retryable; permanent/poison leaves eligibility through terminal, quarantine, error-store, or manual-recovery disposition; intentional indefinite retryable paths need governed recovery |
| Caller 500 after retries; dependency status empty or generic | D — Failure disposition | Permanent 4xx not retried; 401 only if auth refreshes; diagnostics must survive attempt reset (log/durable/nested cause), not only rolled-back vars |
| MUnit green; production empty or alternate id fields | A — Fixture fidelity | Cover normal and representative adverse production shapes, not Studio convenience alone |
| Fix deployed; previously failed ids still not re-delivered | E — State | Watermark/dedupe hold; source re-emit or operational recovery |
| Multi-hop try always blames writeback | D — Attribution | Result flag only after first hop; separate error subjects |
| Cache-miss ERROR storms or Object Store failures | E — Object Store | Separate expected `KEY_NOT_FOUND`, availability fallback, and invalid key/null/configuration errors; encode keys |

When the signature matches Class D disposition gaps, fix classification first: permanent/poison
must leave the eligible loop through terminal, quarantine, error-store, or manual-recovery
disposition. Intentional indefinite retryable recovery needs backoff, monitoring, ownership,
recovery criteria, and replay/manual recovery—not only higher dependency capacity.

### Deploy-related bursts

Compare error windows with deployment and replica events. Lifecycle or event-after-stop signatures
close to a rolling transition can support a deployment-related hypothesis, but timestamps alone do
not prove it.

Before proposing suppression or `on-error-continue`, verify acknowledgement, persistence,
redelivery, idempotency, and message-loss behavior. Never claim that a message will be reprocessed
after swallowing an error unless the queue and source semantics prove it.

### Memory pressure

Compare heap baseline after GC, allocation slope, full-GC activity, payload size, concurrent work,
batch settings, queue depth, and replica divergence. A repeated sawtooth is normally collection
activity; a rising post-GC baseline is only a leak hypothesis until retention evidence supports it.

Check for:

- full-payload logging or repeated serialization
- large repeatable in-memory streams
- oversized variables or queue messages
- high batch or parallel concurrency
- unbounded caches or object-store usage
- connector or custom-code resource retention

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
