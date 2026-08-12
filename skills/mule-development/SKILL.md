---
name: mule-development
description: Create or modify MuleSoft Mule 4 flows, DataWeave, error handling, connectors, queues, batch jobs, configuration, and tests using evidence-based project conventions and post-change validation. Use whenever implementing or reviewing Mule application source changes. Inspect runtime and connector versions before applying version-sensitive guidance, and preserve existing contracts unless the user requests a breaking change.
---

# MuleSoft Development Best Practices

Develop against the current project's Mule runtime, connector versions, contracts, conventions,
deployment target, and operational constraints. Treat the examples as patterns to adapt and verify,
not project-independent guarantees.

Design and validate changes against five invariant classes. The post-development checklist is the
verification surface for the same classes—not a second tutorial.

| Class | Owns |
| --- | --- |
| **A — Value contracts** | Shape, type, media type, and fixture fidelity at each boundary |
| **B — Expression embedding** | `#[…]` still complete after XML/CDATA parsing |
| **C — Contract authority** | What APIKit actually routes vs files on disk |
| **D — Failure disposition** | Permanent vs retryable, terminal state, honest attribution |
| **E — State and idempotency** | Caches, sources, watermarks, hashes, event shapes |

## Privacy and reuse boundary

- Never copy project, organization, application, endpoint, payload, identifier, schedule, volume, or
  incident details from one client into a reusable skill or another project.
- Use neutral roles and synthetic data in examples. Keep secrets, tenant details, private hosts,
  personal data, and production payloads out of source comments, fixtures, logs, and documentation.
- Derive a reusable rule from prior incidents only after separating the general mechanism from the
  original topology and observed values.

## Before editing

1. Read repository instructions and the owning flow, referenced flows, contract, DataWeave,
   configuration keys, error strategy, and relevant MUnit tests.
2. Confirm Mule runtime, Java, and connector versions before using version-sensitive syntax.
3. Identify the behavioral contract, error semantics, delivery guarantees, and operational signals
   that must remain stable.
4. Prefer the smallest coherent change and preserve unrelated formatting and manual content.
5. Decide how the change will be tested before implementation.

---

## Class A — Value contracts

A value's media type, nullability, and structural shape must match the **next consumer**, not the
last processor that happened to work in Studio.

### Pin media type for the next consumer

- Multi-branch expressions (`if`/`else`, `match`) that can return different media types need an
  explicit `output` directive so DataWeave does not fail with media-type inference errors.
- HTTP `targetValue`, set-variable expressions, and log string concatenations that mix typed vars
  (for example `application/java` and `application/json`) need a pinned `output` (often
  `application/java` or `text/plain`) and `as String` when building text.
- Prefer one stable media type for a variable's entire lifetime in the flow.

```dataweave
%dw 2.0
output application/java
---
if (!isEmpty(vars.knownId))
  vars.knownId as String
else
  (vars.lookup."@internalId" default vars.lookup.internalId default "") as String
```

### Serialization boundaries

| Location | Guidance |
| --- | --- |
| In-memory variable | Prefer the native type needed by downstream processors |
| Batch record or variable | Use simple serializable values; test across step boundaries |
| HTTP body inside a batch step | Emit the request media type expected by the endpoint; JSON is commonly appropriate |
| Persistent VM queue | Confirm platform support and serialize only simple supported values |

Avoid retaining lazy iterators, streams, map views (including filter results that yield entry views),
or connector-specific objects across a batch step or persistent queue. JSON or another
connector-ready byte representation is often safer for outbound HTTP bodies **inside**
`<batch:step>` because some Java collection views are not batch-serializer friendly.

### Null vs empty

DataWeave `default` applies when the left side is **null or the field is absent**. It does **not**
treat a present empty string or empty collection as missing:

```dataweave
// ✅ absent or null @id falls through to .id
vars.record."@id" default vars.record.id

// ❌ present empty string does NOT fall through
// if @id is "", this expression stays ""
vars.record."@id" default vars.record.id

// ✅ first non-empty when empty string is possible
if (!isEmpty(vars.record."@id")) vars.record."@id"
else if (!isEmpty(vars.record.id)) vars.record.id
else ""
```

Use `isEmpty` / first-non-empty selection when connectors or conversions can yield `""` rather than
null or absence.

### Dual representations and known keys

Connectors may expose the same identifier as an XML attribute, a bean property, both, or neither
after conversion. Prefer an **already-known request key** (the id you queried by) over re-deriving
from an ambiguous response. When a system-facing app owns the response shape, normalize once at
that boundary so callers do not guess.

### Typed coercions

Emit the type the target API accepts. A value that "looks numeric" as a JSON string can still fail
a Number field. Coerce deliberately (`as Number`) or null out non-numeric input; do not rely on
implicit string forms.

### Fixture fidelity

MUnit fixtures must exercise the **worst-case production shape**, not the convenient Studio shape.
If production returns an empty or alternate accessor for an id, the mock must do the same so tests
cannot green-wash the fallback path.

### DataWeave recipes

Keep everyday transforms short and null-safe where optional data is allowed.

Null-safe object fields:

```dataweave
%dw 2.0
output application/java
---
{
    entityName: payload.entity.name default "Unknown",
    contactAddress: payload.entity.contact.address default null
}
```

Filter and map:

```dataweave
%dw 2.0
output application/java
---
payload.records filter ($.status == "ACTIVE") map {
    recordId: $.id,
    amount: $.totalAmount
}
```

### Scatter-gather

After `scatter-gather`, results are keyed by route index as strings (`payload.'0'.payload`). Save
the original message before scatter-gather when later processors need it.

### Imports and identifiers

- Import `try` from `dw::Runtime` when calling `try()`.
- Unquoted identifiers must start with a letter; later characters may include underscores. Quote
  output keys that need a leading underscore or special characters.

---

## Class B — Expression embedding integrity

Mule evaluates `#[…]` only when the runtime still sees a **complete** expression after XML parsing.

### CDATA and expression terminators

Inside `<![CDATA[…]]>`, the expression's closing `]` must come **before** the CDATA terminator
`]]>`. If the expression ends with `}` and you write `}]]>`, the CDATA ends early: the `]` that
should close `#[` is consumed by the markup, Mule treats the value as a **literal String**, and
connectors that expect a Map/MultiMap fail at runtime—while XML remains well-formed and packaging
succeeds.

```xml
<!-- ❌ Wrong terminator pattern: expression ] is swallowed by CDATA end; runtime sees a String -->
<!-- Shape: ... } ]]>   (only two ] before >) -->
<http:query-params><![CDATA[#[output application/java
---
{ id: vars.recordId }
]]></http:query-params>

<!-- ✅ Expression closes with ], then CDATA ends with ]]> -->
<!-- Shape: ... } ] ]]>  (three ] before >) -->
<http:query-params><![CDATA[#[output application/java
---
{ id: vars.recordId }
]]]></http:query-params>
```

Correct sibling blocks in the same file do not prove the edited path is valid. After changing
`query-params`, `headers`, or `uri-params` CDATA, verify the body starts with `#[` and ends with
`]` immediately before `]]>`.

---

## Class C — Contract authority and route reality

### Bound contract is what routes

For APIKit projects, the runtime validates against the **bound** contract referenced by
`apikit:config` (or equivalent)—not an unbound file sitting elsewhere in the repo.

Identify how this project binds the contract before changing routes:

| Binding | Authority | When routes change |
| --- | --- | --- |
| Local resource (for example `api="api.raml"` on a file in the app) | That local file is the runtime authority | Edit the bound file and implementing flows; no Exchange publish unless the project also publishes that artifact |
| Published dependency (Exchange / Maven pin + APIKit pointing at that artifact) | The pinned published version | Update source of truth, publish or bump the pin, repoint APIKit if needed, sync any human-facing local copy, align consumers |

Never treat an unreferenced local RAML/OAS as runtime authority when APIKit binds a different
artifact. Packaging success is not route proof.

### Bidirectional inventory

| Drift | Typical symptom |
| --- | --- |
| Bound contract resource/method without implementing flow | `APIKIT:NOT_IMPLEMENTED` (often HTTP 501); startup "no implementation" / FlowFinder warnings |
| Requested path absent from bound contract | `APIKIT:NOT_FOUND` / HTTP 404 before business logic |
| Path present in bound contract, method not allowed | `APIKIT:METHOD_NOT_ALLOWED` / HTTP 405 |
| Implementing flow with no matching bound resource | Dead path; not selected by APIKit for any client request |
| Renamed path or method only on one side | 404, 405, or not-implemented after cutover depending which side lagged |

Cross-check resources, methods, parameters, media types, status codes, and error envelopes both
ways.

---

## Class D — Failure disposition

Every meaningful failure path needs a **classified** outcome and an honest system of record.

### Propagate vs continue

```xml
<error-handler>
    <on-error-propagate type="HTTP:CONNECTIVITY">
        <logger level="ERROR" message="Service unavailable"/>
    </on-error-propagate>
    <on-error-continue type="HTTP:TIMEOUT">
        <logger level="WARN" message="Request timed out, using fallback"/>
        <set-payload value='#[vars.fallbackData]'/>
    </on-error-continue>
</error-handler>
```

Use `on-error-continue` only when the caller or source may legitimately see success or when
asynchronous disposition is deliberate. Use `on-error-propagate` when failure must surface.

### Permanent vs retryable

Classify before retrying:

| Usually permanent | Usually retryable |
| --- | --- |
| Client 4xx such as 400, 403, 404, 405 | 429, 5xx, connectivity, timeouts |
| 401 when credentials cannot change between attempts | 401 only when each attempt refreshes token, signature, or other auth material |

Misclassifying a permanent error as "retry next scheduler run" causes unbounded error logs and
records that never leave the eligible set. Misclassifying a transient error as permanent drops work.

### Attempt budgets for async work

When the **application** re-selects the same business record on a schedule or poll (eligible query /
watermark / status gate), decide an explicit disposition policy for permanent failures and for
long-running retryable failures:

- **Bounded retry** (required when permanent errors or poison records must leave the eligible set):
  durable attempt counter, max attempts, terminal business state when exhausted, and protected
  writeback for that terminal mark.
- **Indefinite retry of only retryable errors** (allowed when evidenced): keep the record eligible
  until the dependency recovers, but still classify permanent errors so they do not loop forever.
- Do not force a terminal state on transient-only paths merely to "have a budget"—that converts
  recoverable work into permanent loss.

When a **queue or event source** already provides bounded redelivery and a dead-letter (or equivalent)
terminal disposition, prefer that source-native policy. Do not invent Object Store counters or
business-record writebacks solely because a listener can fail—document acknowledgement, max
redelivery, and DLQ (or project equivalent) instead.

Never log that work "will retry" unless eligibility, redelivery, or the next trigger actually
includes it.

### Retry wrappers must stay transparent

Inside `until-successful` or equivalent:

- Do **not** retry permanent client errors.
- Retry 429/5xx/connectivity when the operation is safe and idempotent (or otherwise retriable).
  Prefer backoff or jitter so concurrent records and replicas do not amplify dependency load.
- Retry **401 only when each attempt can refresh** credentials, OAuth tokens, or request signatures.
  Static, invalid, or revoked credentials remain permanent—idempotency alone is not enough.
- When retrying auth-sensitive calls, regenerate per-attempt tokens or signatures as the dependency
  requires.
- Failed attempts often **reset payload and variables** before the next try and after exhaustion, so
  storing status only in ordinary event vars can leave the outer handler with bare
  `MULE:RETRY_EXHAUSTED`. Preserve diagnostics with in-attempt logging, an `on-error-continue` path
  that builds a durable/error response before exit, Object Store or similar when required, or by
  reading nested cause information the runtime still exposes—verify for the installed version.

### Multi-hop attribution

When one `<try>` spans dependency call A and writeback B, do not hardcode "B failed." Gate success
and system-of-record messages on evidence that A completed (for example a result variable set only
after A returns). Discriminate A vs B failures in error subjects and payloads.

### Structured error contracts

If a shared error-logging flow reads `payload.RecordId`, producers must send `RecordId`—not a
display label. Wrong keys silently drop triage fields.

### Silent skip ban

Choice guards that only log and skip without a durable error signal, metric, or intentional
business disposition hide outages. Business-impactful skips need a durable signal.

### Partial failure in loops and batch

`on-error-propagate` inside `foreach` aborts remaining items. Use `on-error-continue` on **foreach
item work** when one item's failure must not cancel the rest, and log each failure with enough
context to reprocess.

Do **not** apply that foreach rule blindly to `<batch:step>`. Batch already isolates failed records
from successful ones according to batch job settings; wrapping step work in `on-error-continue` can
mark a record as successfully handled and hide the failure from batch error handling. Prefer batch
accept/failure policies and step-level error design documented for the installed runtime.

### Defensive error payload access

`error.errorMessage` payloads may be absent, binary, text, or structured. Parse inside `try()` and
log only sanitized fields:

```dataweave
%dw 2.0
import try from dw::Runtime
output application/java
var parsed = try(() -> read(error.errorMessage.payload, "application/json"))
---
if (parsed.success) parsed.result else {}
```

### VM listener shutdown

Rolling transitions can produce lifecycle signals while components stop. Treat as a delivery
problem: confirm acknowledgement, persistence, and redelivery before `on-error-continue`. Never
claim automatic reprocessing without queue and source evidence.

### Error type strings

Use `error.errorType.identifier`, not `.asString`.

---

## Class E — State, sources, and idempotency

### Object Store misses and keys

An `os:retrieve` without a non-null default throws `OS:KEY_NOT_FOUND`. A default that evaluates to
`null` also throws—do not use `#[null]`. For cache-aside, use a non-null sentinel or handle only
`OS:KEY_NOT_FOUND` in a Try scope; keep store-unavailable failures visible when the store is
required.

```xml
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue">
    <os:default-value><![CDATA[#[{ "cacheMiss": true }]]]></os:default-value>
</os:retrieve>
```

Keys and values must be store-legal types for the installed Object Store. Binary material from
`Crypto::hashWith` (or similar) usually needs a hex or string encoding before use as a key. When
cache is optional, degrade to the source of record on store errors instead of failing the business
transaction.

Bound `maxEntries` / TTL from measured usage; do not reuse another project's cache size. When multiple
replicas or overlapping schedulers update the same key (attempt counters, idempotency tokens), design
for concurrent writers—plain retrieve-modify-store can lose updates.

### Sources and watermarks

Polling and modified-object sources may default flags that other operations set explicitly (for
example body-fields-only style options). Confirm defaults for the **installed connector version**
against sibling operations in the same app.

Dedupe and watermark stores can hold identifiers after a failed processing attempt. A successful
deploy does not automatically re-deliver those records until the source re-emits them (re-modify,
replay, or operational recovery). Document recovery for business-critical paths.

### Content-hash and skip-list discipline

When a project uses content hashes to break sync feedback loops:

- Hash exactly the fields the **outbound transform consumes**.
- **Add** a field to the transform without hashing it → genuine changes can **skip silently**
  (false negative).
- **Remove** a field from the transform but leave it in the hash → unrelated changes still bust the
  cache and cause **unnecessary outbound writes** (false positive / churn), not silent skips.
- Disposition skip-lists (for example "already synced / not applicable") are not content hashes;
  document TTL and invalidation separately.

Record project-specific hash registries in `AGENTS.md`, not in this reusable skill.

### Event payload nesting

Streaming or replay wrappers may nest business fields (for example under `payload.data.payload`).
Read the project's verified listener shape; do not assume top-level `payload.field`.

### Streaming reconnection

Finite reconnect counts can permanently drop long-lived listeners after session invalidation. When
continuous listen is required, use the connector's continuous reconnection strategy and verify it
for the installed version.

### Idempotent creates

Prefer natural or external identifiers (or upsert) so a failed writeback after a successful remote
create does not create duplicates on retry.

---

## Flow design

### Separation of concerns

- When the project uses API-led layers, keep channel, orchestration, and system access in their
  evidenced owning layers.
- Do not force API-led layering onto event-driven, batch-only, or deliberately consolidated apps.

### Private flow vs subflow

| Use a source-less Flow when... | Use a Subflow when... |
| --- | --- |
| The unit needs its own error handler | The unit should share the caller's error strategy |
| An independently named boundary helps ops | The unit is lightweight synchronous composition |

Neither construct implies a transaction boundary—configure transactions explicitly.

### Naming

Follow repository convention. Use stable, purpose-based names without client, environment, or
deployment identity. Before renaming, update every `flow-ref`, test, log query, alert, and document.

| Type | Example pattern |
| --- | --- |
| Scheduler | `record-sync-scheduler-flow` |
| Listener | `source-record-listener-flow` |
| Queue listener | `work-queue-listener-flow` |
| Private flow | `validate-record-flow` |
| Subflow | `processItemsSubFlow` |

---

## Concurrency, timeouts, and connections

- `numberOfConsumers` = queue pollers; `maxConcurrency` = concurrent flow executions. When
  `maxConcurrency` is below consumer count, treat it as deliberate back pressure or a review signal.
- Calculate effective concurrency across consumers, flow limits, parallel scopes, batch settings,
  replicas, pools, and dependency quotas.
- Batch block size is a memory and scheduling control, not a direct count of simultaneous dependency
  calls.
- Prefer explicit connection pool bounds when the connector and dependency capacity require them.
  Verify special values (for example "unlimited") for the installed version.
- Distinguish connect, response, read, connection-idle, proxy, retry, and total upstream deadlines.
  Ensure synchronous inner work, retries, and error mapping fit the caller deadline with margin.
- Connection idle timeout governs **unused** persistent connections; it is not a substitute for
  response/read timeout on an active request. Do not apply a universal `idleTimeout >=
  responseTimeout` rule across unrelated components. Verify each timer against the installed
  connector documentation.

```xml
<!-- Serial only when ordering, non-idempotent writes, or downstream limits require it -->
<flow name="scheduled-job-queue-listener" maxConcurrency="1">
    <vm:listener queueName="scheduledJobQueue" numberOfConsumers="1" config-ref="vm-config"/>
</flow>
```

Keep queue messages minimal: pass only fields the consumer needs.

### HTTP method body mode

For GET, HEAD, or OPTIONS, rely on verified connector behavior for the installed version, or set
`sendBodyMode="NEVER"` when the project needs an explicit guarantee that no body is sent. Do not
add it mechanically when `AUTO` already matches the connector.

---

## Query and connector inputs

Validate required identifiers before building dynamic queries. Null or empty values can become the
literal `'null'` or invalid syntax. Escape or bind using the connector's mechanism. Select every
field downstream transforms consume—missing fields become silent nulls. Handle empty results, null
results, pagination (or intentional single-page limits), and connector-specific result shapes.

```xml
<choice>
  <when expression="#[!isEmpty(vars.recordId)]">
    <!-- build and run query -->
  </when>
  <otherwise>
    <logger level="WARN" message="Skipping query — recordId empty"/>
  </otherwise>
</choice>
```

---

## Logging and correlation

| Level | Use |
| --- | --- |
| ERROR | Failed transactions |
| WARN | Degraded or retryable paths |
| INFO | Business milestones |
| DEBUG | Detailed execution (non-prod by default) |

Log minimal safe operational fields. Do not log full payloads or secrets. Verify structured logger
fields name the correct enclosing flow. Keep logger or app version properties aligned with the
packaged artifact when the project emits a version.

Verify inbound correlation adoption and outbound propagation before promising end-to-end traceability.

---

## Invariant index

| ❌ Avoid | ✅ Prefer | Class |
| --- | --- | --- |
| Unpinned multi-branch media types or mixed typed concat | Explicit `output` for next consumer | A |
| Present empty string treated as `default` fallback | `isEmpty` / first-non-empty when `""` is possible; `default` still covers null/absent | A |
| Fixtures that hide prod shape | Worst-case prod shape in MUnit | A |
| CDATA that truncates `#[…]` | Expression `]` before `]]>` | B |
| Unbound local file treated as runtime contract | Bound `apikit:config` artifact + bidirectional route check | C |
| Unbounded retry of permanent/poison/unclassified errors | Classify errors; bound poison paths; document intentional indefinite retryable recovery | D |
| Hardcoded "writeback failed" for multi-hop try | Attribute the hop that failed | D |
| Retry all errors; read status from retry wrapper only | Capture status in-attempt; skip permanent 4xx; 401 only if auth refreshes | D |
| Business skip with log only | Durable error or intentional disposition signal | D |
| `#[null]` OS default; Binary OS keys | Non-null sentinel; string/hex keys; degrade optional cache | E |
| Assuming deploy reprocesses watermarked ids | Document source re-emit / recovery | E |
| Hash out of sync with outbound fields | Add→hash (avoid silent skip); remove→drop from hash (avoid churn) | E |
| Full records on VM queues | Minimal consumer fields | — |
| SOQL with unguarded variables | Validate inputs; select consumed fields | — |

---

## Post-development checklist

After modifying or creating any flow, **read and run**
`resources/post-development-checklist.md`. It verifies Classes A–E plus privacy, concurrency, and
build hygiene:

- **High** — privacy/secrets, Classes B–D, batch serialization, delivery loss, unbounded load
- **Medium** — Class A residual, Class E, timeouts, concurrency, queues, correlation
- **Low** — naming, imports, version strings, docs

> **Directive:** Every time you finish editing a Mule flow:
> 1. Open `resources/post-development-checklist.md` and verify the changed path against the class
>    checks. Pay special attention to High items.
> 2. Update project documentation (`docs/`, `AGENTS.md`) when behavior, invariants, or recovery
>    steps changed.

## Version-sensitive references

Re-check official documentation when runtime or connector versions differ:

- [DataWeave identifier rules](https://docs.mulesoft.com/dataweave/latest/dataweave-language-introduction#rules-for-declaring-valid-identifiers)
- [Batch processing and concurrency](https://docs.mulesoft.com/mule-runtime/latest/tuning-batch-processing)
- [Object Store connector reference](https://docs.mulesoft.com/object-store-connector/latest/object-store-connector-reference)
- [VM Connector behavior and deployment limitations](https://docs.mulesoft.com/vm-connector/latest/)
- [HTTP Connector reference](https://docs.mulesoft.com/http-connector/latest/http-documentation)
