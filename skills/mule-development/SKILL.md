---
name: mule-development
description: Create or modify MuleSoft Mule 4 flows, DataWeave, error handling, connectors, queues, batch jobs, configuration, and tests using evidence-based project conventions and post-change validation. Use whenever implementing or reviewing Mule application source changes. Inspect runtime and connector versions before applying version-sensitive guidance, and preserve existing contracts unless the user requests a breaking change.
---

# MuleSoft Development Best Practices

Develop against the current project's Mule runtime, connector versions, contracts, conventions,
deployment target, and operational constraints. Treat the examples as patterns to adapt and verify,
not project-independent guarantees.

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

## DataWeave Patterns

### Null-Safe Navigation
```dataweave
{
    entityName: payload.entity.name default "Unknown",
    contactAddress: payload.entity.contact.address default null
}
```

### Array Filtering and Mapping
```dataweave
payload.records filter ($.status == "ACTIVE") map {
    recordId: $.id,
    amount: $.totalAmount,
    items: $.lineItems map {
        sku: $.productCode,
        quantity: $.qty
    }
}
```

### Grouping and Aggregation
```dataweave
payload groupBy $.category mapObject ((value, key) -> {
    (key): {
        count: sizeOf(value),
        totalAmount: sum(value.amount)
    }
})
```

### Conditional Logic
```dataweave
{
    discount: if (payload.amount > 1000) 0.1
              else if (payload.amount > 500) 0.05
              else 0,
    priority: payload.type match {
        case "URGENT" -> "HIGH"
        case "NORMAL" -> "MEDIUM"
        else -> "LOW"
    }
}
```

### Scatter-Gather Payload Access
After a `scatter-gather`, results are keyed by route index as strings:
```dataweave
// Access results from a 3-route scatter-gather
var sourceResult = payload.'0'.payload    // first route
var ruleResult   = payload.'1'.payload    // second route
var targetResult = payload.'2'.payload    // third route
```
> **Caution:** Scatter-gather replaces the current `payload`. If you need the original payload after scatter-gather, save it to a variable first (`set-variable`) and restore it afterward (`set-payload`).

### DWL Imports
Some DataWeave functions require explicit imports:
```dataweave
// try() — must import from dw::Runtime
import try from dw::Runtime
var result = try(() -> payload.nested.value)
---
result.success

// Coercions and string utilities
import * from dw::util::Coercions
import * from dw::core::Strings
```
> **Gotcha:** `try()` will throw a compile error if you forget the import. Always add `import try from dw::Runtime` at the top of the DWL script.

### Field Naming Rules
DataWeave field identifiers must follow strict naming rules:
```dataweave
// ✅ Correct — starts with a letter; later characters can include underscores
{
    resolvedEntity: vars.entity,
    sourceId: payload.id,
    target2Name: payload.name
}

// ❌ Invalid — underscore prefix violates naming rules
{
    _resolvedEntity: vars.entity,    // ERROR: starts with _
    _cache: {},                        // ERROR: starts with _
}

// To use special characters in keys, quote them:
{
    ("_resolvedEntity"): vars.entity  // OK when the output key requires it
}
```
> **Rule:** Unquoted identifiers must start with a letter. Later characters can include letters,
> numbers, and underscores. Quote output keys that require other characters or a leading underscore.

### Choose the Output Media Type Deliberately

For values used only in memory, `application/java` can avoid unnecessary JSON serialization. For
values crossing a batch, persistent queue, connector, or other serialization boundary, confirm that
the resulting value is serializable on the target runtime and connector version:
```dataweave
%dw 2.0
output application/java
---
payload.items map { id: $.id, name: $.name }
```

### Preserve Serializable Values Across Batch Steps

An incident can occur when a batch record contains an internal Java collection view that the batch
serializer cannot reconstruct. JSON or another connector-ready byte representation is often a safe
choice for an outbound HTTP body inside a batch step, but the correct media type depends on the
connector contract and where the value is retained.

| Location | Guidance |
| --- | --- |
| In-memory variable | Prefer the native type needed by downstream processors |
| Batch record or variable | Use simple serializable values; test across step boundaries |
| HTTP body inside a batch step | Emit the request media type expected by the endpoint; JSON is commonly appropriate |
| Persistent VM queue | Confirm platform support and serialize only simple supported values |

Avoid retaining lazy iterators, streams, map views, or connector-specific objects across a batch
step. Add an MUnit or representative runtime test when changing media type or materialization.

---

## Error Handling

### On Error Propagate
Use when you want to handle an error but still propagate it to the caller:
```xml
<error-handler>
    <on-error-propagate type="HTTP:CONNECTIVITY">
        <logger level="ERROR" message="Service unavailable"/>
    </on-error-propagate>
</error-handler>
```

### On Error Continue
Use when you want to handle an error and continue normal execution:
```xml
<error-handler>
    <on-error-continue type="HTTP:TIMEOUT">
        <logger level="WARN" message="Request timed out, using fallback"/>
        <set-payload value='#[vars.fallbackData]'/>
    </on-error-continue>
</error-handler>
```

### Try Scope for Selective Error Handling
```xml
<try>
    <http:request config-ref="HTTP_Config" path="/external-api"/>
    <error-handler>
        <on-error-continue type="HTTP:TIMEOUT">
            <set-payload value='#[{"status": "timeout"}]'/>
        </on-error-continue>
    </error-handler>
</try>
```

### VM Listener Shutdown Behavior

Rolling transitions can produce lifecycle or event-after-stop signals when a source dispatches work
while components are stopping. Treat this as a delivery-semantics problem, not merely log noise.

Before changing the error handler:

1. Confirm the error aligns with a deployment or stop event.
2. Determine whether the queue is transient or persistent and whether persistence is supported on
   the deployment target.
3. Verify acknowledgement, redelivery, idempotency, and message-loss behavior.
4. Prefer source lifecycle and graceful-shutdown corrections where available.
5. Use `on-error-continue` only when swallowing the error cannot acknowledge or discard work that
   still needs processing.

Never log that a message "will be reprocessed" unless the configured source and queue semantics
prove that claim.

### Error Type References
Always use `.identifier` for error type strings, not `.asString`:
```dataweave
// ✅ Correct
"Error Type: " ++ (error.errorType.identifier default "UNKNOWN")

// ❌ Wrong — .asString does not exist
"Error Type: " ++ error.errorType.asString
```

---

## Flow Design

### Separation of Concerns
- When the project uses API-led layers, keep channel concerns, orchestration, and system access in
  their evidenced owning layers.
- Do not force API-led layering onto event-driven, batch-only, or deliberately consolidated apps.
- Keep contract mapping, orchestration, and connector-specific logic separable even when they live
  in one deployable application.

### Private vs Sub Flows
| Use a source-less Flow when... | Use a Subflow when... |
| --- | --- |
| The called unit needs its own error handler | The unit should share the caller's error strategy |
| The unit benefits from an independently named processing boundary | The unit is lightweight synchronous composition |
| The project convention favors a private flow for reusable behavior | The project convention favors a subflow |

Do not assume either construct creates a transaction boundary. Configure transactions explicitly
and verify connector participation.

### Breaking Down Complex Flows
```
main-flow (API endpoint)
  ├── validate-request-subflow
  ├── enrich-data-flow (private)
  ├── transform-data-subflow
  ├── call-system-api-flow (private)
  └── format-response-subflow
```

Consider decomposition when a flow mixes responsibilities, hides alternate paths, is difficult to
test, or repeats logic. Component count is a review signal, not a hard threshold.

---

## Naming Conventions

### Example Convention
| Type | Pattern | Example |
|------|---------|--------|
| Scheduler | `<entity>-<action>-scheduler-flow` | `record-sync-scheduler-flow` |
| Listener | `<source>-<entity>-listener-flow` | `source-record-listener-flow` |
| Queue Listener | `<queue-role>-listener-flow` | `work-queue-listener-flow` |
| Private Flow | `<action>-<entity>-flow` | `validate-record-flow` |
| Sub Flow | `<action><Entity>SubFlow` | `processItemsSubFlow` |

For new flows, follow the repository's established convention unless the user requests a broader
cleanup. Use stable, purpose-based names without client, environment, or deployment identity. Before
renaming an existing flow, update every `flow-ref`, test, log query, alert, and document that treats
the name as an operational identifier.

---

## Concurrency Basics

- `numberOfConsumers` on a VM listener = how many threads poll the queue
- `maxConcurrency` on the flow = how many threads can execute the flow simultaneously
- When `maxConcurrency` is below the source consumer count, some consumers cannot execute
  concurrently. Treat this as a deliberate back-pressure choice or a configuration smell, not an
  automatic correctness failure.
- Calculate effective concurrency across consumers, flow limits, parallel scopes, batch settings,
  replicas, connection pools, and downstream capacity.

### Choose Queue Concurrency from Delivery Requirements

Use serial processing only when ordering, non-idempotent writes, shared state, or downstream limits
require it:

```xml
<!-- Serial only when the workload requires it -->
<flow name="scheduled-job-queue-listener" maxConcurrency="1">
    <vm:listener queueName="scheduledJobQueue" numberOfConsumers="1" config-ref="vm-config"/>
</flow>
```

Before selecting a value, verify trigger overlap, replica behavior, queue distribution, persistence
support on the deployment target, ordering, idempotency, recovery, throughput targets, and
dependency quotas. Schedulers can still require parallelism, and event-driven consumers can still
require serialization.

### Connection Pooling
- Make pool behavior deliberate. Prefer an explicit bound when the connector supports it and the
  dependency has known capacity constraints.
- Size the pool from measured concurrency, replica count, request duration, and documented
  dependency limits. Do not reuse a numeric limit from another project.
- Verify whether a connector's special values mean unlimited, runtime-managed, or something else
  for the installed version.

### Timeouts
- Distinguish connect, response, read, connection-idle, proxy, retry, and total request deadlines.
- Set requester response timeouts deliberately when the default does not match the service budget.
- For synchronous chains, ensure inner calls, retries, and error mapping can finish with margin
  before the upstream deadline.
- Do not compare a persistent connection's idle lifetime to a request response deadline as if they
  governed the same behavior.

---

## SOQL Safety

### Validate Inputs for Dynamic SOQL
Validate required query inputs before concatenation. Null or empty values can create unintended
string literals, invalid syntax, or broader/narrower results than intended. Escape or bind values
using the connector's supported mechanism:
```dataweave
// ❌ Dangerous — if vars.recordId is null, query becomes: "...WHERE Id = 'null'"
"SELECT Id FROM Entity__c WHERE Id = '" ++ vars.recordId ++ "'"

// ✅ Safe — guard before the HTTP call
<choice>
  <when expression="#[!isEmpty(vars.recordId)]">
    <!-- proceed with SOQL query -->
  </when>
  <otherwise>
    <logger level="WARN" message="Skipping query — recordId is null"/>
  </otherwise>
</choice>
```

### Include All Fields Used Downstream
SOQL queries must include every field that downstream DWL transforms or mappings reference. Missing fields cause silent `null` values:
```dataweave
// ❌ Query only selects Id, but DWL uses ParentId__c
"SELECT Id FROM Entity__c WHERE ..."
// downstream: vars.entity.ParentId__c  →  null!

// ✅ Include all fields needed
"SELECT Id, ParentId__c FROM Entity__c WHERE ..."
```

---

## ObjectStore Patterns

### Handle Expected Object Store Misses Explicitly

An `os:retrieve` without a non-null default throws `OS:KEY_NOT_FOUND` when the key is absent. A
default expression that resolves to `null` also throws, so do not use `#[null]` as the default. In a
cache-aside pattern, use a non-null sentinel or handle `OS:KEY_NOT_FOUND` explicitly. In workflows
where a missing key is exceptional, preserve the error.

```xml
<!-- Cache miss raises OS:KEY_NOT_FOUND -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue"/>

<!-- Cache-aside option: use a non-null sentinel -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue">
    <os:default-value><![CDATA[#[{ "_cacheMiss": true }]]]></os:default-value>
</os:retrieve>
```

For a cache-aside default, guard the downstream logic:
```xml
<choice>
    <when expression='#[!(vars.cachedValue."_cacheMiss" default false)]'>
        <logger level="DEBUG" message="Cache hit"/>
    </when>
    <otherwise>
        <!-- Fetch from system of record and store in cache -->
        <http:request .../>
        <os:store key="#[vars.cacheKey]" objectStore="my-cache-store">
            <os:value><![CDATA[#[payload]]]></os:value>
        </os:store>
    </otherwise>
</choice>
```

Alternatively, catch only `OS:KEY_NOT_FOUND` in a Try scope, set an explicit miss flag, and perform
the source lookup after the scope. Keep other Object Store failures visible.

---

## Logging and Correlation

### Log Levels
| Level | Use Case |
|-------|----------|
| ERROR | Exceptions, failed transactions |
| WARN | Degraded functionality, fallback scenarios |
| INFO | Business events, API calls, major milestones |
| DEBUG | Detailed flow execution (dev/test only) |

### Avoid Logging Full Payloads
Logging entire payloads can expose sensitive data and consume heap. Log only the minimal safe
operational fields, and hash or redact identifiers when required by policy:
```dataweave
// ✅ Good
"Processing entity type: " ++ (payload.type default "unknown")

// ❌ Avoid
write(payload, "application/json")
```

---

## Common Pitfalls

| ❌ Don't | ✅ Do |
|----------|------|
| Store large payloads in variables | Use streaming |
| Hard-code URLs/credentials | Externalize in properties |
| Leave a meaningful boundary without an effective error strategy | Verify local or global handling and caller outcome |
| Carry lazy or connector-specific objects across batch steps | Materialize simple serializable values and test the boundary |
| Change batch HTTP bodies to Java objects without testing | Preserve the endpoint media type and verify batch serialization |
| Accept unbounded connection behavior accidentally | Choose and document a version-valid pool strategy |
| Log entire payloads or raw identifiers | Log minimal safe operational context |
| Reuse one timeout value for every timer | Build an end-to-end deadline budget |
| Use `_` prefix in DWL field names (e.g. `_cache`) | Start field names with a letter (e.g. `resolvedCache`) |
| Build SOQL with potentially null variables | Null-guard variables before constructing SOQL |
| Use `try()` without importing it | Add `import try from dw::Runtime` |
| Forget to restore payload after scatter-gather | Save to variable before, restore after |

---

## Post-Development Checklist

After modifying or creating any flow, **read and run through** the checklist in `resources/post-development-checklist.md`. It contains common gotchas discovered from production incidents, organized by severity:

- 🔴 **High** — unsafe error handlers, contract changes, serialization failures, delivery loss,
  secrets, and unbounded load
- 🟡 **Medium** — timeout budgets, concurrency, query inputs, queue payloads, correlation, and
  operational signals
- 🟢 **Low** — unused imports, naming drift, stale versions, and documentation gaps

> **Directive:** Every time you finish editing a Mule flow:
> 1. Open `resources/post-development-checklist.md` and verify your changes don't introduce any of the listed gotchas. Pay special attention to the 🔴 High severity items.
> 2. Check whether any project documentation (`docs/`, `AGENTS.md`) needs updating to reflect your changes.

## Version-sensitive references

Re-check the current official documentation when runtime or connector versions differ from the
project where a pattern was learned:

- [DataWeave identifier rules](https://docs.mulesoft.com/dataweave/latest/dataweave-language-introduction#rules-for-declaring-valid-identifiers)
- [Batch processing and concurrency](https://docs.mulesoft.com/mule-runtime/latest/tuning-batch-processing)
- [Object Store connector reference](https://docs.mulesoft.com/object-store-connector/latest/object-store-connector-reference)
- [VM Connector behavior and deployment limitations](https://docs.mulesoft.com/vm-connector/latest/)
- [HTTP Connector reference](https://docs.mulesoft.com/http-connector/latest/http-documentation)
