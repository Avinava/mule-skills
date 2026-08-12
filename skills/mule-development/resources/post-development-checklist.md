# Post-Development Checklist

Run after every Mule source or contract change. Apply checks relevant to the changed path, but
always complete scope/privacy, security/configuration, contract authority, failure disposition,
validation, and final-diff review.

This is the verification surface for
[Invariant classes and cross-cutting gates](../references/invariant-classes.md), not a tutorial.
Prioritize by credible project impact and evidence; do not infer severity from the class label.

| Class | Verification question |
| --- | --- |
| **A** | Do values match the next consumer's shape, type, media type, nullability, and serialization contract? |
| **B** | Is every embedded `#[…]` complete after XML/CDATA parsing? |
| **C** | Does the authoritative API/event contract agree with reachable implementation and consumers? |
| **D** | Is every failure classified, observable, correctly attributed, and deliberately dispositioned? |
| **E** | Are cache, source, watermark, replay, hash, and duplicate behaviors intentional? |

## Contents

1. [Scope, privacy, and security](#1-scope-privacy-and-security)
2. [Class A — Value contracts](#2-class-a--value-contracts)
3. [Class B — Expression embedding](#3-class-b--expression-embedding)
4. [Class C — Contract authority and reachability](#4-class-c--contract-authority-and-reachability)
5. [Class D — Failure disposition](#5-class-d--failure-disposition)
6. [Class E — State and idempotency](#6-class-e--state-and-idempotency)
7. [Cross-cutting runtime and delivery gates](#7-cross-cutting-runtime-and-delivery-gates)
8. [Build, tests, and documentation](#8-build-tests-and-documentation)
9. [Impact scan](#9-impact-scan)

## 1. Scope, privacy, and security

- Confirm only intended files, contracts, and behaviors changed; preserve unrelated user work.
- Confirm no prior-client identity, topology, endpoint, payload, identifier, schedule, volume,
  incident detail, or tuning value entered source, comments, fixtures, logs, or documentation.
- Confirm no secret, token, secure-property value/ciphertext, private host, tenant identifier,
  personal data, local machine path, or production payload was added or exposed.
- Verify authentication, authorization, TLS/trust, policy assumptions, input trust, least privilege,
  secure-property use, and environment configuration for changed boundaries.
- Confirm required property keys exist in templates and deployment inputs without opening values.
- Use synthetic, structurally representative test data.

## 2. Class A — Value contracts

- Make `output` explicit when mixed input media types, inference mismatch, or the next consumer's
  writer contract requires it; do not add it mechanically to every branch.
- Confirm each variable, `targetValue`, connector parameter, header/query/URI map, and payload matches
  the next consumer's shape, type, media type, and nullability.
- Remember `default` covers null/absent values, not present empty strings or collections. Use
  first-non-empty only where empty is equivalent to missing.
- Validate required values before side effects; do not silently null invalid required data.
- Prefer known request identifiers over ambiguous response accessors; normalize at the owning
  boundary when appropriate.
- Coerce values to accepted target types and handle coercion failure deliberately.
- Keep batch/queue values simple and supported. Avoid lazy iterators, streams, map/entry views, and
  connector-specific objects across serialization boundaries.
- Preserve the outbound endpoint's media type for HTTP bodies inside batch steps and run a
  representative target-runtime serialization test when the representation changes.
- Test normal production shape and relevant adverse/alternate shapes; mocks must be capable of
  failing the changed mechanism.
- Validate query inputs, bind/escape user-derived values, select every downstream-consumed field,
  and handle empty/null results and pagination.
- Verify scatter-gather indexes and preserve the original message when later work needs it.
- Confirm required DataWeave imports and valid quoted/unquoted identifiers.

## 3. Class B — Expression embedding

- Run:

  ```bash
  python3 .agents/skills/mule-development/scripts/check_embedded_expressions.py .
  ```

- For each changed CDATA body beginning with `#[`, confirm its trimmed content ends with `]` before
  `]]>` (`}]]]>`, not `}]]>`, when the body ends with `}`).
- Inspect changed direct XML attribute expressions and non-CDATA embedding separately.
- Do not use packaging success or a valid sibling block as evaluation proof.

## 4. Class C — Contract authority and reachability

- Identify the authoritative boundary: APIKit-bound local contract, published Exchange/Maven pin,
  event schema, connector metadata, or another evidenced source.
- For a local APIKit binding, change the bound file and implementation; publish only if the project
  already publishes that artifact.
- For a published binding, update its source, publish/bump, update the pin/configuration, synchronize
  intentional copies, and coordinate consumers.
- Inventory resources/events in both directions. For APIKit, distinguish absent path (typically
  404), absent method (typically 405), bound route without implementation (typically 501), and
  implementation not selected by APIKit.
- Before calling an APIKit-unbound flow dead, check sources, all `flow-ref` callers, evidenced dynamic
  conventions, configuration, and tests.
- Verify paths/topics, methods/operations, parameters, headers, security, schemas, payload nesting,
  media types, examples, status codes, and error envelopes.
- Trace renames through flow references, contracts/schema versions, tests, consumers, policies,
  logs, alerts, dashboards, and documentation.
- For events and queues, verify publisher/consumer compatibility, acknowledgement, ordering,
  redelivery, deduplication, and side effects; mark APIKit checks not applicable when appropriate.

## 5. Class D — Failure disposition

- Classify changed failures as permanent, retryable, or explicitly context-dependent before retry.
- Do not retry permanent validation/client/business failures. Retry 401 only when every attempt can
  refresh auth material; validate actual connector error types.
- Honor idempotency, total caller deadline, dependency quota, and `Retry-After`/backoff guidance.
- For app-driven re-selection:
  - permanent/poison records leave the eligible loop through terminal, quarantine/error-store, or
    deliberate manual-recovery disposition;
  - bounded retryable policies use durable atomic attempts/deadlines and protected exhaustion
    handling;
  - intentional indefinite retryable policies include backoff, monitoring, escalation/ownership,
    recovery criteria, and replay/manual recovery.
- For queue/event sources, prefer and document existing redelivery/DLQ behavior; verify
  acknowledgement, max redelivery, replay, ordering, duplicates, and loss before adding counters or
  swallowing errors.
- For `until-successful`, catch only permanent types inside and turn them into a classified successful
  scope result; let retryable types escape for retry. Handle permanent disposition after the scope.
- Preserve diagnostics through failed-attempt resets with in-attempt logging, durable capture, or
  verified nested cause—not only ordinary variables.
- Attribute the operation actually reached and failed in multi-hop Try scopes; gate success messages
  on evidence that preceding operations completed.
- Confirm structured error keys match their consumer and logger flow/operation names are correct.
- Give business-impactful skips a durable signal, metric, or intentional disposition.
- Parse error payloads defensively and sanitize them; avoid error-handler double faults.
- Keep `foreach` per-item continuation distinct from batch record failure policy; do not hide batch
  failure with mechanical `on-error-continue`.
- Deduplicate or distinguish originating failure, retry summary, structured error, and default
  listener logs.
- Never claim automatic retry/reprocessing without source, eligibility, or queue evidence.

## 6. Class E — State and idempotency

- Treat `OS:KEY_NOT_FOUND` as an expected miss only for an evidenced optional/cache-aside path; use a
  non-null default or catch that type explicitly.
- Allow optional-cache fallback on availability failures such as `OS:STORE_NOT_AVAILABLE` only with
  a degraded signal and safe load on the source of record.
- Surface invalid/blank keys, null values, security/configuration failures, and programming errors;
  never convert every Object Store error into a miss.
- Use store-legal String keys, encode Binary hashes, and exclude secrets, personal data, and
  unnecessary raw payloads from keys and values.
- Verify TTL, `maxEntries`, persistence, deployment support, multi-replica behavior, stale-data
  policy, and atomicity. A retrieve-modify-store sequence can lose concurrent updates.
- Verify polling/source defaults for the installed connector when downstream fields depend on them.
- Document recovery when watermark/dedupe state prevents failed identifiers from being re-emitted.
- Keep content-hash inputs aligned with outbound transform fields; manage skip-list TTL/invalidation
  separately.
- Verify event wrapper nesting, continuous reconnection, replay, and duplicate behavior.
- Keep create/upsert side effects idempotent across retry, redelivery, and failed writeback.

## 7. Cross-cutting runtime and delivery gates

- Calculate effective concurrency across source consumers, `maxConcurrency`, parallel scopes, batch,
  replicas, pools, and dependency limits. Derive numbers from current evidence.
- Treat batch block size as memory/scheduling, not request concurrency; bound streaming,
  materialization, variables, and payload logging for memory safety.
- Budget connect, response/read, idle, proxy, retry, and total caller deadlines correctly; idle
  connection lifetime is not active response timeout.
- Verify connection-pool special values and deployment-target compatibility for installed versions.
- Keep queue messages minimal, serializable, and free of unnecessary sensitive data.
- Verify transient/persistent VM support, acknowledgement, recovery, and duplicate/loss semantics on
  the actual deployment target.
- Confirm transactions are explicit where needed and every connector's participation, commit, and
  rollback behavior is understood; flows/subflows do not create implicit transaction boundaries.
- For GET, HEAD, and OPTIONS, use verified connector body behavior or an explicit no-body mode when
  required by contract.
- Verify inbound correlation adoption and outbound propagation before claiming end-to-end tracing.
- Match operational version metadata to the packaged artifact.

## 8. Build, tests, and documentation

- Run the embedded-expression checker for XML changes, then project formatter/linter, focused MUnit,
  and the required integration/package gate.
- Cover success and meaningful failure/disposition paths with assertions that can detect the actual
  mechanism.
- Re-run contract/schema validation and route/event mapping checks; packaging alone is insufficient.
- Update contracts, schemas, operations guidance, diagrams, recovery notes, `AGENTS.md` invariants,
  and changelog when behavior changes.
- Review the final diff for unsupported assumptions, unrelated edits, stale links, copied identity,
  and accidental generated artifacts.
- Report commands, outcomes, skipped checks, tool failures, and remaining evidence gaps.

## 9. Impact scan

Escalate based on credible consequence in the current path:

| Consequence | Examples to scan |
| --- | --- |
| Security, privacy, data/message loss | Exposed values; unsafe trust boundary; swallowed delivery; non-recoverable state |
| Incorrect results, outage, contract break | Wrong types/shapes; broken bound route; retry storm; duplicate side effects |
| Reliability or operability degradation | Missing terminal/recovery signal; stale cache; unsupported VM persistence; timeout mismatch |
| Maintainability/documentation | Stale names, imports, versions, runbooks, links, or project invariants |

## Project-local additions

Keep project-specific checks in the consuming repository. Promote lessons upstream only after
removing identity and expressing the reusable mechanism.
