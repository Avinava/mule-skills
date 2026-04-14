---
name: mule-development
description: Best practices for developing MuleSoft Mule 4 applications — DataWeave patterns, flow design, error handling, naming conventions, and validation. Use this skill every time you are modifying or creating a flow.
---

# MuleSoft Development Best Practices

This skill provides reference patterns and conventions for developing Mule 4 applications.

---

## DataWeave Patterns

### Null-Safe Navigation
```dataweave
{
    customerName: payload.customer.name default "Unknown",
    email: payload.customer.contact.email default null
}
```

### Array Filtering and Mapping
```dataweave
payload.orders filter ($.status == "ACTIVE") map {
    orderId: $.id,
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
var projectResult  = payload.'0'.payload    // first route
var contactResult  = payload.'1'.payload    // second route
var invoiceResult  = payload.'2'.payload    // third route
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
// ✅ Correct — starts with alpha, alphanumeric only
{
    resolvedProject: vars.project,
    contactId: payload.Id,
    account2Name: payload.Name
}

// ❌ Invalid — underscore prefix violates naming rules
{
    _resolvedProject: vars.project,    // ERROR: starts with _
    _cache: {},                        // ERROR: starts with _
}

// To use special characters in keys, quote them:
{
    ("_resolvedProject"): vars.project  // OK but non-standard
}
```
> **Rule:** Field names must start with a letter (`Alpha`) followed by zero or more alphanumeric characters (`AlphaNumeric`). No leading underscores, hyphens, or numbers.

### Use `application/java` for In-Memory Variables
When a transform result will be stored in a variable (especially one entering a batch scope), use `output application/java` instead of `output application/json` to avoid streaming value warnings:
```dataweave
%dw 2.0
output application/java
---
payload.items map { id: $.id, name: $.name }
```

### ⚠️ NEVER Use `application/java` for HTTP Payloads Inside Batch Steps
While `application/java` is correct for **variables**, outbound HTTP request **payloads** inside `<batch:step>` must stay `output application/json`. The Mule BatchEngine uses Kryo to serialize `payload` between batch steps, and DataWeave's Java collection types (`LinkedHashMap$LinkedValues`) are not Kryo-serializable — causing 100% batch failure with `BatchException` on every record.

| Location | `application/java` | `application/json` |
|----------|:-:|:-:|
| Variables entering batch scope | ✅ | ❌ |
| HTTP payloads in normal flows | ✅ | ✅ |
| HTTP payloads inside `<batch:step>` | ❌ **NEVER** | ✅ |

> **Why:** JSON payloads serialize into simple byte arrays that Kryo handles natively. Java collections from DataWeave contain internal iterator references and view types that Kryo's reflective serializer cannot reconstruct.

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

### VM Listener Shutdown Error Handler (Rolling Deploys)
VM queue listeners will continue pulling messages during a rolling deploy shutdown. When the flow is mid-teardown, components throw `LifecycleException: "X" is stopped`. Without an error handler, these produce 100+ ERROR entries per deploy.

**Pattern:** Add a two-branch error handler to every VM queue listener flow:
```xml
<flow name="my-queue-listener" maxConcurrency="1">
    <vm:listener queueName="myQueue" numberOfConsumers="1" config-ref="vm-config"/>
    <!-- ... flow logic ... -->
    <error-handler>
        <!-- Branch 1: Swallow deploy shutdown noise -->
        <on-error-continue type="ANY"
            when='#[error.description contains "is stopped" or error.description contains "LifecycleException"]'>
            <logger level="WARN" message="Deploy shutdown — message will be reprocessed by new replica"/>
        </on-error-continue>
        <!-- Branch 2: Real errors → log + persist -->
        <on-error-continue type="ANY">
            <logger level="ERROR" message="Processing error"/>
            <flow-ref name="errorLogFlow"/>
        </on-error-continue>
    </error-handler>
</flow>
```

> **Why this matters:** Without this pattern, a deploy can produce 100+ `LifecycleException` errors in a 2-second burst, inflating error metrics and masking real issues.

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
- **API Layer**: Handles requests/responses, orchestration
- **Process Layer**: Business logic, transformations
- **System Layer**: Direct system connections, CRUD operations

### Private vs Sub Flows
| Use Private Flows when... | Use Sub Flows when... |
|---------------------------|----------------------|
| You need separate error handling | You want to share parent's error handling |
| The logic is reusable across flows | Simple code organization |
| You want transaction boundaries | No need for separate transaction scope |

### Breaking Down Complex Flows
```
main-flow (API endpoint)
  ├── validate-request-subflow
  ├── enrich-data-flow (private)
  ├── transform-data-subflow
  ├── call-system-api-flow (private)
  └── format-response-subflow
```

Flows with >15-20 components should be broken down.

---

## Naming Conventions

### Preferred Convention
| Type | Pattern | Example |
|------|---------|--------|
| Scheduler | `<entity>-<action>-scheduler-flow` | `order-sync-scheduler-flow` |
| Listener | `sfListener-<entity>-sync-flow` | `sfListener-check-sync-flow` |
| Queue Listener | `<queue-name>-listener` | `job-queue-listener` |
| Private Flow | `<action>-<entity>-flow` | `validate-payment-flow` |
| Sub Flow | `<action><Entity>SubFlow` | `processItemsSubFlow` |

**Rules for new flows:**
- Use kebab-case for flow names
- End with `-flow` or `-subflow`
- Keep under 50 characters
- Do not rename legacy flows — the names are embedded in log correlation and monitoring

---

## Concurrency Basics

- `numberOfConsumers` on a VM listener = how many threads poll the queue
- `maxConcurrency` on the flow = how many threads can execute the flow simultaneously
- **Rule:** `maxConcurrency` should be ≥ `numberOfConsumers`, otherwise consumers are wasted

### Scheduler Queue Concurrency: Serial per Replica
For VM queues that receive messages from **schedulers** (not real-time events), set both `maxConcurrency="1"` and `numberOfConsumers="1"`:

```xml
<!-- ✅ Scheduler-driven queue: serial per replica -->
<flow name="scheduled-job-queue-listener" maxConcurrency="1">
    <vm:listener queueName="scheduledJobQueue" numberOfConsumers="1" config-ref="vm-config"/>
</flow>
```

**Why serial?**
1. **Replicas provide parallelism** — With 2 replicas, there are already 2 consumers processing in parallel across the cluster
2. **Race condition safety** — Multiple consumers per replica competing for the same queue during shutdown causes `LifecycleException` bursts (see Error Handling section)
3. **Schedulers don't need speed** — Scheduler batches run every 30 min; a few seconds of serial processing per replica has zero impact on SLA

**When to use higher concurrency:** Only for event-driven queues (e.g., platform event-fed VM queues) where latency matters and the downstream system can handle parallel requests.

### Connection Pooling
- Always set explicit `maxConnections` — never use `-1` (unlimited)
- Match pool size to downstream system limits (e.g., NetSuite SOAP allows ~3-8 concurrent connections)

### Timeouts
- `idleTimeout` must be ≥ `responseTimeout` — if idle timeout fires first, Grizzly kills the connection mid-request, causing silent failures
- Always set explicit `responseTimeout` on HTTP requesters
- Align timeouts across tiers: PAPI → SAPI → External System

---

## SOQL Safety

### Always Null-Guard Dynamic SOQL
When building SOQL queries from variables, null/empty values produce malformed queries that return 400 errors:
```dataweave
// ❌ Dangerous — if vars.recordId is null, query becomes: "...WHERE Id = 'null'"
"SELECT Id FROM Check__c WHERE Id = '" ++ vars.recordId ++ "'"

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
// ❌ Query only selects Id, but DWL uses AccountId
"SELECT Id FROM Contact WHERE ..."
// downstream: vars.contact.AccountId  →  null!

// ✅ Include all fields needed
"SELECT Id, AccountId FROM Contact WHERE ..."
```

---

## ObjectStore Patterns

### Always Use `<os:default-value>` on Retrieve
An `os:retrieve` without a default value throws `OS:KEY_NOT_FOUND` on cache misses. In a cache-aside pattern, a miss is **normal** — the flow should fall through to the system-of-record lookup, not throw an error.

```xml
<!-- ❌ Cache miss throws OS:KEY_NOT_FOUND → pollutes error metrics -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue"/>

<!-- ✅ Cache miss returns null → flow falls through cleanly -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache-store" target="cachedValue">
    <os:default-value><![CDATA[#[null]]]></os:default-value>
</os:retrieve>
```

Then guard the downstream logic:
```xml
<choice>
    <when expression="#[vars.cachedValue != null]">
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

> **Common issue:** ObjectStore cache misses without `<os:default-value>` can produce multiple `OS:KEY_NOT_FOUND` errors per day, inflating error metrics even though the flow works correctly.

---

## Logging

### Log Levels
| Level | Use Case |
|-------|----------|
| ERROR | Exceptions, failed transactions |
| WARN | Degraded functionality, fallback scenarios |
| INFO | Business events, API calls, major milestones |
| DEBUG | Detailed flow execution (dev/test only) |

### Avoid Logging Full Payloads
Logging entire JSON payloads consumes significant heap. Extract specific identifiers instead:
```dataweave
// ✅ Good
"Processing order: " ++ payload.orderId

// ❌ Avoid
write(payload, "application/json")
```

---

## Common Pitfalls

| ❌ Don't | ✅ Do |
|----------|------|
| Store large payloads in variables | Use streaming |
| Hard-code URLs/credentials | Externalize in properties |
| Skip error handling on flows | Add error handlers to every flow |
| Use `output application/json` for batch variables | Use `output application/java` |
| Use `output application/java` for HTTP payloads inside `<batch:step>` | Keep `output application/json` — Kryo can't serialize DW Java collections |
| Set `maxConnections="-1"` | Set explicit connection limits |
| Log entire payloads | Log IDs and key fields only |
| Mismatched timeout configs across tiers | Align timeouts (upstream ≤ downstream) |
| Use `_` prefix in DWL field names (e.g. `_cache`) | Start field names with a letter (e.g. `resolvedCache`) |
| Build SOQL with potentially null variables | Null-guard variables before constructing SOQL |
| Use `try()` without importing it | Add `import try from dw::Runtime` |
| Forget to restore payload after scatter-gather | Save to variable before, restore after |

---

## Post-Development Checklist

After modifying or creating any flow, **read and run through** the checklist in `resources/post-development-checklist.md`. It contains common gotchas discovered from production incidents, organized by severity:

- 🔴 **High** — Unsafe error payload access, missing `try()` imports, null SOQL variables, connection pool misconfig
- 🟡 **Medium** — Batch variable materialization, concurrency mismatches, VM queue payload bloat
- 🟢 **Low** — Unused imports, GET body warnings, version mismatches

> **Directive:** Every time you finish editing a Mule flow:
> 1. Open `resources/post-development-checklist.md` and verify your changes don't introduce any of the listed gotchas. Pay special attention to the 🔴 High severity items.
> 2. Check whether any project documentation (`docs/`, `AGENTS.md`) needs updating to reflect your changes.
