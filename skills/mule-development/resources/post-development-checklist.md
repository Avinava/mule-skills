# Post-Development Checklist

Common gotchas discovered from production incidents and fix sessions. **Run through this checklist after any flow modification before building.**

---

## 1. Error Handler Safety

### ❌ Unsafe `error.errorMessage.payload` Access
Directly accessing `error.errorMessage.payload` crashes when the error payload is `Binary` (e.g., from HTTP responses). This causes a **double-fault** — the error handler itself throws `MULE:EXPRESSION`.

```dataweave
// ❌ CRASHES on Binary payloads
var sapiPayload = error.errorMessage.payload

// ✅ Safe — use try() + read() + write()
import try from dw::Runtime
var rawPayload = try(() -> write(error.errorMessage.payload, "application/json"))
var sapiPayload = if (rawPayload.success)
    read(rawPayload.result, "application/json") default {}
  else {}
```

### ❌ Wrong `flowName` in Error Logger Content
Error handler `json-logger:content` blocks sometimes hardcode the wrong flow name (copy-paste from another flow). This makes production error triage much harder.

**Check:** Every `json-logger:content` inside an error handler references the correct enclosing flow name.

### ❌ Missing Error Handler on Flows
Every flow that does meaningful work should have an `<error-handler>`. Unhandled errors silently propagate and get swallowed in queue-driven architectures.

---

## 2. DataWeave

### ❌ Missing `import try from dw::Runtime`
Using `try()` without the explicit import causes a **compile error** at deploy time, not at design time.

```dataweave
// ❌ Compiles in Studio, fails at runtime
var result = try(() -> payload.value)

// ✅ Always import
import try from dw::Runtime
var result = try(() -> payload.value)
```

### ❌ Unused DW Imports
Leaving `import * from dw::core::Strings` when nothing from that module is used adds noise. However, **be careful not to remove imports that ARE used** (e.g., `substring()` requires `dw::core::Strings`).

Common functions that do NOT need `dw::core::Strings`:
- `isEmpty()`, `isBlank()` — these are core DataWeave functions

Functions that DO need `dw::core::Strings`:
- `substring()`, `capitalize()`, `camelize()`

### ❌ `output application/json` for Batch Variables
Variables entering a batch scope must use `output application/java`. Using `application/json` creates streaming values that cause Kryo serialization warnings and potential data loss.

```dataweave
// ❌ Creates streaming values in batch
%dw 2.0
output application/json
---
payload.items map { id: $.id }

// ✅ Materializes to plain Java objects
%dw 2.0
output application/java
---
payload.items map { id: $.id }
```

### ❌ `output application/java` for HTTP Payloads Inside Batch Steps
**NEVER** change outbound HTTP request payloads inside `<batch:step>` from `application/json` to `application/java`. While `application/java` works fine for variables and for HTTP payloads in **normal flows**, inside batch steps the Mule BatchEngine uses **Kryo** to serialize the current `payload` between steps. DataWeave's internal Java collection types (e.g., `LinkedHashMap$LinkedValues`, `LinkedHashMap$LinkedEntrySet`) are **not Kryo-serializable**, causing:

1. `ExternalizableKryo` WARN — "Reflective operation exception found when creating an implicit reflection serializer"
2. `com.mulesoft.mule.runtime.module.batch.exception.BatchException` on every record
3. **100% batch failure** — all records route to `on-complete` with error status

```xml
<!-- ❌ CRASHES inside <batch:step> — Kryo can't serialize Java LinkedHashMaps -->
<ee:transform doc:name="Prepare Update">
    <ee:set-payload><![CDATA[%dw 2.0
output application/java
---
[{ "Id": vars.record.Id, "Status__c": "Cleared" }]]]></ee:set-payload>
</ee:transform>
<http:request method="POST" config-ref="http-request-config" .../>

<!-- ✅ CORRECT — JSON byte arrays serialize cleanly through Kryo -->
<ee:transform doc:name="Prepare Update">
    <ee:set-payload><![CDATA[%dw 2.0
output application/json
---
[{ "Id": vars.record.Id, "Status__c": "Cleared" }]]]></ee:set-payload>
</ee:transform>
<http:request method="POST" config-ref="http-request-config" .../>
```

> **Why:** JSON payloads serialize into simple byte arrays that Kryo handles natively. Java collections from DataWeave contain internal iterator references and view types that Kryo's reflective serializer cannot reconstruct.

**The rule:**
| Location | Use `application/java`? | Use `application/json`? |
|----------|:-:|:-:|
| Variables entering batch scope | ✅ Yes | ❌ No |
| HTTP payloads in normal flows | ✅ OK | ✅ OK |
| HTTP payloads inside `<batch:step>` | ❌ **NEVER** | ✅ Yes |

### ❌ Field Names Starting with `_`
DataWeave field identifiers must start with a letter. Leading underscores cause runtime errors.

```dataweave
// ❌ Runtime error
{ _resolvedProject: vars.project }

// ✅ Correct
{ resolvedProject: vars.project }
```

### ❌ Accessing Payload After Scatter-Gather
Scatter-gather **replaces** the payload. If you need the original payload downstream, save it to a variable first.

```xml
<!-- ✅ Save before scatter-gather -->
<set-variable value="#[payload]" variableName="originalPayload" />
<scatter-gather>
    <route> ... </route>
    <route> ... </route>
</scatter-gather>
<!-- Access results: payload.'0'.payload, payload.'1'.payload -->
```

---

## 3. SOQL and Salesforce

### ❌ Null Variables in SOQL
A null variable produces `WHERE Id = 'null'` which returns 400 errors, not empty results.

```xml
<!-- ✅ Always guard -->
<choice>
  <when expression="#[!isEmpty(vars.recordId)]">
    <!-- proceed with SOQL -->
  </when>
  <otherwise>
    <logger level="WARN" message="Skipping — recordId is null"/>
  </otherwise>
</choice>
```

### ❌ Missing Fields in SOQL SELECT
If downstream DWL references `vars.contact.AccountId`, the SOQL query **must** include `AccountId` in the SELECT. Missing fields cause **silent nulls**, not errors.

```sql
-- ❌ DWL downstream uses AccountId but it's not selected
SELECT Id FROM Contact WHERE ...

-- ✅ Include all downstream fields
SELECT Id, AccountId FROM Contact WHERE ...
```

---

## 4. Concurrency and Connections

### ❌ `maxConcurrency` < `numberOfConsumers`
If `maxConcurrency="1"` but `numberOfConsumers="2"`, the second consumer thread is permanently blocked — wasted resources and misleading config.

**Rule:** `maxConcurrency` ≥ `numberOfConsumers` on VM listener flows.

### ❌ `maxConnections="-1"` (Unlimited)
Never use unlimited connections. This leads to `Max connections exceeded` errors when the downstream system's internal pool exhausts.

**Rule:** Always set an explicit `maxConnections` value matched to the downstream system's capacity.

### ❌ `idleTimeout` < `responseTimeout`
If `idleTimeout` fires before `responseTimeout`, Grizzly kills the TCP connection mid-request, causing **silent HTTP failures** — no error, no response, no log.

**Rule:** `idleTimeout` ≥ `responseTimeout` on all HTTP request configs.

---

## 5. VM Queues

### ❌ Full Records in VM Queue Payload
Passing entire raw records (e.g., `record: item.record`) through VM queues bloats message size and wastes memory. Only pass the fields needed by the consuming flow.

```dataweave
// ❌ Passes entire record
{ record: item.record, id: item.id }

// ✅ Extract only needed fields
{ id: item.id, name: item.name, amount: item.amount }
```

---

## 6. ObjectStore

### ❌ ObjectStore Retrieve Without Default Value
An `os:retrieve` without `<os:default-value>` throws `OS:KEY_NOT_FOUND` on cache misses. In cache-aside patterns, misses are normal — they should return null, not throw errors.

```xml
<!-- ❌ Cache miss throws OS:KEY_NOT_FOUND -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache" target="result"/>

<!-- ✅ Cache miss returns null -->
<os:retrieve key="#[vars.cacheKey]" objectStore="my-cache" target="result">
    <os:default-value><![CDATA[#[null]]]></os:default-value>
</os:retrieve>
```

---

## 7. HTTP Requests

### ❌ Body on GET Requests
HTTP GET requests that include a body produce `Body is ignored` warnings. While this is cosmetic (a one-time-per-thread Mule runtime message), prevent it with:

```xml
<http:request method="GET" sendBodyMode="NEVER" ... />
```

> **Note:** This warning self-suppresses after the first occurrence per thread. If you already have `sendBodyMode="NEVER"` and still see it once per startup, that's expected Mule runtime behavior — not a bug.

---

## 8. Build and Deploy

### ❌ Version Mismatch
`json.logger.application.version` in property files (`prod.yaml`, `dev.yaml`, `local.yaml`) must match `pom.xml <version>`. A mismatch means production logs report the wrong version, making incident triage unreliable.

### ❌ Unimplemented APIkit Routes
If the RAML spec defines an endpoint but no implementation flow exists, Mule logs a WARN on every startup:
```
FlowFinder - Action-Resource-ContentType triplet has no implementation -> post:/entity:application/json
```

Either remove unused endpoints from the RAML, or stub them with a 501 response.

---

## Quick-Scan Summary

| # | Check | Severity |
|---|-------|----------|
| 1 | Error handlers use `try()/read()/write()` for error payloads | 🔴 High |
| 2 | `import try from dw::Runtime` present when `try()` is used | 🔴 High |
| 3 | SOQL variables null-guarded before query construction | 🔴 High |
| 4 | `maxConnections` is explicit (not `-1`) | 🔴 High |
| 5 | `idleTimeout` ≥ `responseTimeout` | 🔴 High |
| 6 | **HTTP payloads inside `<batch:step>` stay `application/json`** (not java) | 🔴 High |
| 7 | Batch **variables** use `output application/java` | 🟡 Medium |
| 8 | `maxConcurrency` ≥ `numberOfConsumers` | 🟡 Medium |
| 9 | SOQL SELECT includes all downstream fields | 🟡 Medium |
| 10 | Error logger `flowName` matches enclosing flow | 🟡 Medium |
| 11 | No full records passed through VM queues | 🟡 Medium |
| 12 | Payload saved before scatter-gather if needed after | 🟡 Medium |
| 13 | DWL field names start with a letter (no `_` prefix) | 🟢 Low |
| 14 | No unused DWL imports | 🟢 Low |
| 15 | GET requests use `sendBodyMode="NEVER"` | 🟢 Low |
| 16 | Version in property files matches `pom.xml` | 🟢 Low |
| 17 | No unimplemented APIkit routes in RAML | 🟢 Low |
| 18 | `os:retrieve` has `<os:default-value>` (cache miss → null, not error) | 🟡 Medium |

---

## Project-Specific Gotchas

<!-- Add your own project-specific gotchas below as you discover them.
Use the same format: ❌ Problem → ✅ Solution, with optional > **Incident:** note -->
