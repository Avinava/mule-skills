# Post-Development Checklist

Run this checklist after every Mule source change. Apply only the checks relevant to the changed
path, but always complete privacy, contract, error, test, and diff review.

## Contents

1. [Scope and privacy](#1-scope-and-privacy)
2. [Contracts and flow behavior](#2-contracts-and-flow-behavior)
3. [Error handling](#3-error-handling)
4. [DataWeave and serialization](#4-dataweave-and-serialization)
5. [Queries and connector inputs](#5-queries-and-connector-inputs)
6. [Concurrency, queues, and batch](#6-concurrency-queues-and-batch)
7. [Timeouts, retries, and connections](#7-timeouts-retries-and-connections)
8. [State and Object Store](#8-state-and-object-store)
9. [HTTP and correlation](#9-http-and-correlation)
10. [Build, tests, and documentation](#10-build-tests-and-documentation)
11. [Quick scan](#11-quick-scan)

## 1. Scope and privacy

- Confirm only intended files and behaviors changed.
- Confirm no prior-client name, topology, endpoint, payload, identifier, schedule, volume, or
  incident detail entered source, comments, fixtures, logs, tests, or documentation.
- Confirm no secret, token, private hostname, tenant identifier, personal data, or production
  payload was added.
- Use synthetic, structurally minimal test data.
- Preserve unrelated user-authored changes and existing conventions.

## 2. Contracts and flow behavior

- Cross-check RAML/OAS or event schema against listeners, APIKit routes, request/response mapping,
  status codes, and error envelopes.
- Verify every changed `flow-ref` resolves and every renamed flow is updated in tests, logs, alerts,
  and documentation.
- Verify all paths: success, alternate branch, empty input, dependency failure, retry exhaustion,
  and local/global error handling.
- Confirm `on-error-continue` produces a deliberate successful continuation or asynchronous
  disposition. Use `on-error-propagate` when the caller or source must observe failure.
- Confirm queue acknowledgement, redelivery, dead-letter, idempotency, and message-loss behavior
  before swallowing any error.

## 3. Error handling

### Parse error payloads defensively

`error.errorMessage` or its payload can be absent, binary, text, or already structured. Keep risky
access inside `try()` and log only sanitized fields:

```dataweave
%dw 2.0
import try from dw::Runtime
output application/java
var parsed = try(() -> read(error.errorMessage.payload, "application/json"))
---
if (parsed.success) parsed.result else {}
```

- Import `try` from `dw::Runtime` whenever the script calls `try()`.
- Do not serialize and log the whole error payload as a fallback.
- Verify error type access uses supported fields such as `error.errorType.identifier`.
- Verify structured logger content names the correct enclosing flow and operation.
- Deduplicate or clearly distinguish the originating failure, retry summary, error logger, and
  default exception-listener entry.
- Confirm the path has an effective local or global error strategy; do not add handlers solely to
  satisfy a count-based rule.

## 4. DataWeave and serialization

- Confirm unquoted identifiers start with a letter; later characters can include underscores.
  Quote output keys that require special characters or a leading underscore.
- Remove only imports proven unused. Keep module imports required by functions in the script.
- Null-guard optional selectors and avoid defaults that hide required-data errors.
- Save the original message before scatter-gather when later processors need it; address route
  results by their verified route index.
- Choose output media type from the next component's contract.
- Materialize only when needed; avoid retaining lazy iterators, streams, map views, or
  connector-specific objects across batch steps or persistent queues.
- When changing a batch record, variable, or HTTP body between `application/java`, JSON, or another
  type, run a representative serialization test on the target runtime.

## 5. Queries and connector inputs

- Validate required identifiers before building a dynamic query.
- Escape or bind user-derived values using the connector's supported mechanism.
- Confirm selected fields include every field consumed by downstream transforms and conditions.
- Confirm empty results, null results, pagination, and connector-specific result shapes are handled.
- Keep query examples and fixtures entity-neutral; do not copy real object names or identifiers from
  another project.

## 6. Concurrency, queues, and batch

- Calculate effective concurrency from source consumers, flow `maxConcurrency`, parallel scopes,
  batch-job concurrency, replicas, connection pools, and dependency limits.
- Treat `maxConcurrency < numberOfConsumers` as a deliberate back-pressure choice or review signal.
- Treat batch block size as a memory and scheduling control, not a direct count of simultaneous
  dependency calls.
- Select numeric limits from measured workload and documented dependency capacity; do not reuse
  values from another project.
- Keep queue messages minimal and serializable. Pass only fields required by the consumer.
- Verify whether transient or persistent VM queues are supported on the deployment target and match
  the required recovery semantics.
- For lifecycle errors during deployment, verify acknowledgement and redelivery before adding
  `on-error-continue`. Never claim automatic reprocessing without evidence.

## 7. Timeouts, retries, and connections

- Inventory connect, response, read, connection-idle, proxy, retry, and total upstream deadlines.
- Ensure synchronous inner calls, retries, and error mapping fit within the caller's deadline with
  margin.
- Do not compare connection idle lifetime with request response timeout as if they are the same
  timer.
- Bound retries, define retryable errors, and include backoff or jitter where appropriate.
- Confirm retries are safe for the operation's idempotency and do not multiply load beyond the
  dependency's capacity.
- Choose connection-pool behavior deliberately and verify special values against the installed
  connector version.

## 8. State and Object Store

- Decide whether a missing key is expected or exceptional.
- Remember that `os:retrieve` throws `OS:KEY_NOT_FOUND` when no key exists and no non-null default is
  returned. `#[null]` is not a valid miss-suppressing default.
- For cache-aside behavior, use a collision-safe non-null sentinel or handle only
  `OS:KEY_NOT_FOUND` in a Try scope; keep store-unavailable and invalid-key failures visible.
- Verify TTL, persistence, multi-replica access, atomicity, and stale-data behavior.
- Confirm keys and values contain no secret or unnecessary personal data.

## 9. HTTP and correlation

- Confirm request method, path, query parameters, headers, body, and expected media type match the
  contract.
- For GET, HEAD, or OPTIONS, rely on verified connector behavior or set `sendBodyMode="NEVER"` when
  the project needs an explicit guarantee. Do not add it mechanically when `AUTO` already meets the
  installed connector's behavior.
- Verify outbound correlation propagation configuration and inbound adoption before promising
  end-to-end traceability.
- Confirm error mapping preserves a safe correlation reference without returning internal details.
- Avoid raw request/response logging; prefer safe route, outcome, duration, and redacted identifiers.

## 10. Build, tests, and documentation

- Run the project's formatter or linter and focused MUnit tests first, then the required full build.
- Confirm tests cover the changed success path and meaningful failure path rather than only flow
  execution.
- Cross-check API specification routes against implementation and report intentional gaps.
- Match operational version metadata to the packaged artifact when the project logs a version.
- Update owning documentation, diagrams, runbooks, configuration tables, and changelog when behavior
  changed.
- Review the final diff for unsupported assumptions and unrelated edits.

## 11. Quick scan

| Priority | Check |
| --- | --- |
| High | No secrets, client-derived identity, payloads, or private endpoints introduced |
| High | Contract, caller outcome, and queue delivery semantics remain correct |
| High | Error handlers cannot double-fault or silently discard required work |
| High | Batch and queue boundaries contain supported serializable values |
| High | Retry and concurrency cannot exceed the proven dependency budget |
| Medium | Timeout budget covers inner work, retries, and error mapping |
| Medium | Query inputs are validated and all consumed fields are selected |
| Medium | Correlation propagation and log attribution are verified |
| Medium | Object Store miss, TTL, persistence, and failure behavior are intentional |
| Medium | Queue payloads are minimal and recovery behavior is tested |
| Low | Imports, names, versions, docs, and diagrams remain aligned |

## Project-local additions

Keep project-specific checks in the consuming repository, not in this reusable skill. Use neutral
mechanism-based wording if a local lesson is later promoted upstream.
