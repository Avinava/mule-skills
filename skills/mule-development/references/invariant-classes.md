# Invariant classes and cross-cutting gates

## Contents

1. [How to use the model](#how-to-use-the-model)
2. [Class A — Value contracts](#class-a--value-contracts)
3. [Class B — Expression embedding](#class-b--expression-embedding)
4. [Class C — Contract authority and reachability](#class-c--contract-authority-and-reachability)
5. [Class D — Failure disposition](#class-d--failure-disposition)
6. [Class E — State and idempotency](#class-e--state-and-idempotency)
7. [Cross-cutting gates](#cross-cutting-gates)
8. [Invariant index](#invariant-index)

## How to use the model

Apply every class and cross-cutting gate touched by the changed path. The classes overlap: an event
payload can be both a value contract (A) and durable source state (E); a queue failure can involve
value serialization (A), disposition (D), state (E), and delivery semantics.

Do not assign severity by class. Prioritize by the credible consequence in the current project and
the strength of evidence.

## Class A — Value contracts

A value's structural shape, type, media type, nullability, and materialization must match its next
consumer.

### Output media type

DataWeave can infer output when inputs share compatible media types or the receiving field supplies
an expected type. Make `output` explicit when inputs have different media types, inference conflicts
with the next consumer, or the output writer must be guaranteed. Do not require it mechanically for
every conditional expression.

```dataweave
%dw 2.0
output application/java
---
if (!isEmpty(vars.knownId))
  vars.knownId as String
else
  (vars.lookup."@internalId" default vars.lookup.internalId default "") as String
```

Use `application/java` for a native in-memory value when appropriate, `text/plain` for text, or the
wire media type expected by an outbound connector. Prefer one stable media type for a variable's
lifetime.

### Null, empty, and required data

DataWeave `default` applies to null or absent values, not to a present empty string or collection:

```dataweave
// null or absent @id falls through; a present "" does not
vars.record."@id" default vars.record.id

// first non-empty when "" is possible
if (!isEmpty(vars.record."@id")) vars.record."@id"
else if (!isEmpty(vars.record.id)) vars.record.id
else null
```

Use `isEmpty` or first-non-empty selection only where empty is equivalent to missing. Validate and
fail or deliberately disposition missing required values before side effects; do not turn invalid
required data into null merely to avoid an exception.

Connectors can expose one identifier as an attribute, bean property, both, or neither after
conversion. Prefer a known request key over re-deriving it from an ambiguous response. Normalize at
the system-facing boundary when that application owns the response contract.

### Types and serialization

- Coerce to the type the target accepts; a numeric-looking JSON String is not a Number.
- Keep in-memory values native for their consumers.
- Keep batch records and persistent queue messages simple and supported by the target runtime.
- Avoid retaining lazy iterators, streams, map/entry views, or connector-specific objects across a
  batch step or persistent queue.
- For an HTTP body inside a batch step, emit the endpoint's request media type; a connector-ready
  JSON/Binary representation can be safer than an internal Java collection view.
- Verify persistent VM support on the actual deployment target and representative serialization
  across the boundary.

### Fixture fidelity

Cover the normal production shape and every representative adverse or alternate shape relevant to
the changed mechanism. Do not let convenient Studio metadata or mocks hide empty accessors,
alternate nesting, connector-specific values, or serialization boundaries. A fixture must be able
to fail the behavior it claims to test.

### DataWeave and router details

- Save the original Mule message before scatter-gather when later processors need it. Results are
  keyed by route index (`payload.'0'.payload`, and so on); verify indexes against the current routes.
- Import `try` from `dw::Runtime` when calling `try()`.
- Unquoted identifiers start with a letter and can then contain letters, numbers, and underscores.
  Quote keys or selectors that require a leading underscore or special character.
- Remove only imports proven unused and preserve imports required by called functions.

## Class B — Expression embedding

Mule evaluates `#[…]` only when XML parsing leaves a complete expression.

Inside `<![CDATA[…]]>`, close the expression before closing CDATA. When the DataWeave body ends with
`}`, the valid suffix has three closing brackets before `>`: one for `#[…]`, then two for `]]>`.

```xml
<!-- Invalid: CDATA consumes the only closing bracket; Mule receives a literal String -->
<http:query-params><![CDATA[#[output application/java
---
{ id: vars.recordId }
]]></http:query-params>

<!-- Valid: close the expression, then CDATA -->
<http:query-params><![CDATA[#[output application/java
---
{ id: vars.recordId }
]]]></http:query-params>
```

XML can remain well formed and packaging can succeed in the invalid case. Connector Map/MultiMap
conversion failures after editing query parameters, headers, URI parameters, or similar blocks are
an embedding hypothesis until disproven.

Run:

```bash
python3 <skill-root>/scripts/check_embedded_expressions.py .
```

`<skill-root>` is the `mule-development` skill directory:
`${CLAUDE_PLUGIN_ROOT}/skills/mule-development` when installed as a Claude Code plugin,
`.agents/skills/mule-development` when vendored into the project.

The checker scans `src/**/*.xml` CDATA content beginning with `#[` and reports expressions whose
trimmed CDATA body does not end with `]`. Inspect changed direct XML attributes and non-CDATA
expressions separately.

## Class C — Contract authority and reachability

First establish which artifact governs the boundary.

### APIKit authority

For APIKit, the bound contract referenced by `apikit:config` or its equivalent governs routing:

| Binding | Runtime authority | Route-change work |
| --- | --- | --- |
| Local RAML/OAS resource | The referenced local file | Change the bound file and implementation; publish only if the project already publishes it |
| Published Exchange/Maven dependency | The pinned published artifact | Change its source, publish/bump the version, update the pin/configuration, sync intentional copies, and coordinate consumers |

Do not treat an unreferenced local copy as runtime authority. Inventory both directions:

| Drift | Typical APIKit outcome |
| --- | --- |
| Bound resource/method without implementation | `APIKIT:NOT_IMPLEMENTED`, commonly mapped to 501, plus possible startup warnings |
| Requested path absent from bound contract | `APIKIT:NOT_FOUND`, commonly 404 before business logic |
| Path present but method absent | `APIKIT:METHOD_NOT_ALLOWED`, commonly 405 |
| Implementation has no matching bound resource | Not APIKit-routable; inspect other sources and `flow-ref` callers before calling it unreachable or dead |

Cross-check resource paths, methods, parameters, headers, security, request/response schemas, media
types, examples, status codes, and error envelopes. Trace renames through contract source, published
pin, intentional local copies, implementation, tests, consumers, policies, and documentation.

### Event and queue authority

For non-HTTP boundaries, identify the owning event schema, connector metadata, AsyncAPI or other
specification, serialization convention, and version. Verify publisher and consumer in both
directions, including payload/attribute nesting, acknowledgement, ordering, redelivery,
deduplication, compatibility, and side effects. Do not force APIKit checks onto non-API projects.

### Reachability

Build reachability from all sources and call edges. A flow absent from APIKit routing may still be a
scheduler, listener, private source-less flow, or `flow-ref` target. Call something unreachable only
after checking sources, APIKit routes, `flow-ref` edges, dynamic conventions evidenced by the
project, and tests or deployment configuration.

## Class D — Failure disposition

Every meaningful failure needs classification, an observable outcome, and a governed disposition.
Governed does not always mean terminal or numerically bounded.

### Classify before retrying

| Usually permanent | Usually retryable | Context-dependent |
| --- | --- | --- |
| Validation failures; malformed requests; unsupported method/media type; most 400/403/404 | 429; connectivity; timeouts; most 5xx | 401, 408, 409, dependency-specific 4xx, business errors |

- Retry 401 only when each attempt can refresh the credential, token, signature, or other auth
  material. Static invalid or revoked credentials are permanent.
- Respect dependency guidance such as `Retry-After` when available, and apply backoff/jitter where
  concurrent records or replicas could amplify load.
- Retry only when the operation is idempotent, uses an idempotency key, or has another evidenced
  duplicate-safe mechanism.
- Fit synchronous retry work inside the total caller deadline with margin.

### Choose a governed disposition

For application-driven re-selection of business records:

- **Permanent/poison:** remove the record from the eligible loop through a terminal business state,
  quarantine/error store, deliberate manual-recovery state, or another explicit disposition.
- **Bounded retryable:** persist an atomic attempt/deadline budget, stop when exhausted, and protect
  terminal writeback so it cannot silently fail.
- **Intentional indefinite retryable:** allow only classified retryable failures; require backoff,
  monitoring, escalation/ownership, dependency recovery criteria, and a documented replay or manual
  recovery path. Do not add a terminal state that would convert recoverable work into loss.

For a queue or event source that already provides redelivery and dead-letter or equivalent terminal
handling, prefer and document that native mechanism. Do not invent application counters without a
need. Verify acknowledgement point, max redelivery, DLQ behavior, ordering, replay, and duplicates.

Never say work "will retry" unless current eligibility, redelivery, or the next trigger proves it.

### Keep selective retry executable

`until-successful` retries any error that escapes its scope. Every attempt starts with the same
payload and variables that entered the scope; failed-attempt mutations are not visible to the next
attempt. On success, the resulting payload and variables propagate.

To avoid retrying permanent failures while retaining the wrapper for retryable failures:

1. Map connector and business failures to project-specific permanent versus retryable types.
2. Inside `until-successful`, catch only permanent types with `on-error-continue` and produce a
   classified result; let retryable types propagate so the scope retries them.
3. After the scope, inspect the classified result and perform terminal/quarantine/manual-recovery
   disposition or raise the caller-facing error.
4. Capture retry diagnostics in-attempt, durably, or from verified nested causes. Do not depend only
   on failed-attempt variables when handling outer `MULE:RETRY_EXHAUSTED`.

Skeleton—replace error types and disposition with evidenced project behavior:

```xml
<until-successful maxRetries="${dependency.retry.max}"
                  millisBetweenRetries="${dependency.retry.delay}">
  <try>
    <http:request config-ref="dependency-http" path="/resource"/>
    <error-handler>
      <on-error-continue type="HTTP:BAD_REQUEST,HTTP:FORBIDDEN,HTTP:NOT_FOUND">
        <set-variable variableName="failureDisposition" value="PERMANENT"/>
        <set-variable variableName="failureType"
                      value='#[error.errorType.identifier default "UNKNOWN"]'/>
      </on-error-continue>
    </error-handler>
  </try>
</until-successful>
<choice>
  <when expression='#[vars.failureDisposition == "PERMANENT"]'>
    <flow-ref name="disposition-permanent-failure-flow"/>
  </when>
</choice>
```

Do not include 401 in the permanent list if attempts refresh auth, or in the retryable list if they
do not. Validate actual connector error types for the installed version.

### Outcome and attribution

- Use `on-error-continue` only when a successful continuation or asynchronous disposition is
  deliberate. Use `on-error-propagate` when the caller or source must observe failure.
- When one Try contains dependency A and writeback B, gate success and attribution on evidence that A
  completed. Do not hardcode that B failed for every error.
- Match structured error producer keys to the consumer's contract.
- Give business-impactful skip guards a durable signal, metric, or intentional disposition; a log
  alone can hide an outage.
- Parse optional/binary error payloads defensively with `try()` and sanitize output. Use
  `error.errorType.identifier`, not `.asString`.
- Deduplicate or distinguish the originating connector failure, retry summary, structured logger,
  and default exception-listener entry.

### Loop, batch, and lifecycle behavior

- In `foreach`, `on-error-propagate` aborts remaining items. Continue per-item work only when one
  failure must not cancel the rest, and retain actionable reprocessing evidence.
- Do not apply the foreach rule mechanically to `<batch:step>`. Batch has record failure semantics;
  `on-error-continue` can mark a record handled and hide it from batch failure policy.
- For VM or other listener errors during shutdown, verify acknowledgement, persistence, redelivery,
  idempotency, graceful shutdown, and message loss before suppressing the signal.

## Class E — State and idempotency

### Object Store misses, failures, and keys

An absent `os:retrieve` key throws `OS:KEY_NOT_FOUND` unless a non-null default is returned. A default
that resolves to null still throws.

```xml
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue">
  <os:default-value><![CDATA[#[{ cacheMiss: true }]]]></os:default-value>
</os:retrieve>
```

Classify Object Store outcomes:

- Treat `OS:KEY_NOT_FOUND` as an expected miss only when the business path defines cache-aside or
  optional lookup behavior.
- An optional cache may fall back to the source of record on an availability failure such as
  `OS:STORE_NOT_AVAILABLE`, with a degraded signal and bounded load on the source.
- Surface invalid/blank keys, null values, authentication/configuration problems, and programming
  errors. Do not catch every Object Store error as a cache miss.
- Use store-legal String keys. Encode Binary hash output as hex or another stable string form.
- Keep secrets, unnecessary personal data, and raw payloads out of keys and values.

Verify TTL, `maxEntries`, persistence, multi-replica behavior, stale-data policy, and deployment
support. Object Store operations can synchronize per key, but a retrieve-modify-store sequence spans
multiple operations and can still lose concurrent updates; use an atomic design for counters and
idempotency state.

### Sources, watermarks, and replay

Polling and modified-object sources may use connector-version-specific defaults that sibling
operations set explicitly. Verify defaults when downstream identifiers or body fields depend on
them.

Watermark or dedupe state can retain identifiers after processing fails. A successful deployment
does not guarantee re-emission. Document replay, re-modification, watermark recovery, or another
operational path for business-critical records.

### Content hashes and skip lists

When a project uses hashes to prevent sync feedback:

- Hash exactly the fields consumed by the outbound transform.
- Adding a consumed field without hashing it risks a false negative and silent skip.
- Removing a transformed field but leaving it in the hash risks false positives and unnecessary
  writes.
- Treat disposition skip lists separately from content hashes; define TTL and invalidation.

Record project-specific hash registries in that project's `AGENTS.md`, not in this reusable skill.

### Event state and idempotent side effects

- Read the verified listener wrapper and business payload path; do not assume top-level fields.
- For continuous streams, select and verify a connector-version-supported reconnection strategy.
- Prefer natural/external identifiers, upsert, idempotency keys, or duplicate detection so a
  successful remote create followed by failed writeback does not duplicate on retry.
- Make replay behavior explicit for every non-idempotent side effect.

## Cross-cutting gates

### Security and configuration

- Externalize endpoints and credentials; use secure properties and never log values or ciphertext.
- Verify authentication, authorization, TLS/trust, policy assumptions, input validation, and least
  privilege across the full call path.
- Confirm required property keys exist in templates and deployment inputs without opening secrets.
- Use connector-supported binding or escaping for user-derived query values; a presence check alone
  does not prevent injection.

### Capacity and lifecycle

- Calculate effective concurrency from sources, `maxConcurrency`, parallel scopes, batch settings,
  replicas, connection pools, and dependency quotas.
- Treat `maxConcurrency < numberOfConsumers` as deliberate back pressure or a review signal, not an
  automatic defect. Treat batch block size as memory/scheduling, not direct request concurrency.
- Distinguish connect, response/read, connection-idle, proxy, retry, and total upstream deadlines.
  Connection idle timeout governs unused connections, not active request duration.
- Bound streaming/materialization and memory use; avoid full-payload logging and retaining large
  repeatable streams or variables.
- Verify connector pool special values and persistent VM support against installed versions and the
  deployment target.
- For GET, HEAD, and OPTIONS, use verified connector behavior or `sendBodyMode="NEVER"` when the
  project requires an explicit no-body guarantee.

### Delivery and transactions

- Verify acknowledgement, persistence, ordering, redelivery, dead-letter behavior, duplicates, and
  loss before changing handlers or queues.
- Keep queue messages minimal, serializable, and free of unnecessary sensitive data.
- Do not assume a source-less flow or subflow creates a transaction boundary. Configure transactions
  explicitly and verify each connector's participation and rollback behavior.
- Use serial processing only when ordering, shared state, non-idempotent writes, or dependency limits
  require it.

### Flow design

- Follow established project layering; do not force API-led decomposition onto event-driven,
  batch-only, or deliberately consolidated applications.
- Use a source-less Flow when an independently named boundary or local error handler is needed; use a
  Subflow for lightweight synchronous composition that shares the caller's error strategy.
- Decompose mixed responsibilities or hard-to-test alternate paths based on behavior, not component
  count.
- Follow repository naming conventions. Before renaming, update `flow-ref` edges, tests, log queries,
  alerts, dashboards, and documentation.
- Validate query identifiers before construction, bind/escape values, select every consumed field,
  and handle empty/null results and pagination.

### Privacy and observability

- Log minimal safe route, outcome, duration, disposition, and correlation context—never full payloads,
  secrets, personal data, private endpoints, or raw sensitive identifiers.
- Verify inbound correlation adoption and outbound propagation before claiming end-to-end tracing.
- Match logger flow/operation names and application version metadata to the executing flow and
  packaged artifact.
- Use ERROR for failed transactions, WARN for evidenced degradation/retry, INFO for useful business
  milestones, and DEBUG for detailed non-production diagnostics, adapted to project policy.

### Validation and documentation

- Test success and meaningful failure with assertions that can detect the mechanism under review.
- Run lint/static analysis and focused MUnit before the repository-required integration/package gate.
- Packaging does not prove embedded-expression evaluation or contract-route alignment.
- Update contracts, schemas, tests, runbooks, recovery steps, project invariants, and changelog when
  behavior changes.
- Review the final diff for unrelated edits, unsafe assumptions, copied identity, and stale links.

## Invariant index

| Avoid | Prefer | Class/gate |
| --- | --- | --- |
| Ambiguous mixed-media output | Explicit output chosen for the next consumer | A |
| Empty treated as `default`; required data silently nulled | First-non-empty only when allowed; validate required data | A |
| Convenient mocks that hide production variants | Normal and representative adverse fixtures | A |
| Truncated `#[…]` in CDATA | Expression `]` before `]]>` plus deterministic check | B |
| Unbound file treated as runtime authority | Bound contract/schema and bidirectional mapping | C |
| APIKit-unbound flow called dead without reachability | Inspect sources and all call edges | C |
| Retry permanent, poison, or unclassified failures | Classify, selectively retry, and govern disposition | D |
| Indefinite retry without ownership or recovery | Backoff, monitoring, escalation, and replay/manual recovery | D |
| Failure attribution hardcoded to the last hop | Attribute the operation actually reached and failed | D |
| All Object Store errors treated as misses | Separate miss, availability, invalid input, and configuration failures | E |
| Assuming deployment replays watermarked records | Document re-emission and recovery | E |
| Hash fields drift from outbound transform | Keep hash inputs and consumed fields aligned | E |
| Numeric tuning copied from another project | Derive from current capacity and measured workload | Capacity |
| Handler added without delivery proof | Verify acknowledgement, transaction, redelivery, and loss | Delivery |
