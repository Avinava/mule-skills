# Post-Development Checklist

Run after every Mule source change. Apply only checks relevant to the changed path, but always
complete privacy, contract, error disposition, and diff review.

This checklist is the **verification surface** for the five invariant classes in
`../SKILL.md`. It does not restate full tutorials.

| Class | Question |
| --- | --- |
| **A** | Do values match the next consumer's shape, type, and media type? |
| **B** | Is every embedded `#[…]` still complete after XML/CDATA parsing? |
| **C** | Does the bound contract (local file or published pin) match routes both ways? |
| **D** | Is every failure classified, bounded, attributed, and durably signaled? |
| **E** | Are cache, source, watermark, hash, and event-state behaviors intentional? |

## Contents

1. [Scope and privacy](#1-scope-and-privacy)
2. [Class A — Value contracts](#2-class-a--value-contracts)
3. [Class B — Expression embedding](#3-class-b--expression-embedding)
4. [Class C — Contract authority](#4-class-c--contract-authority)
5. [Class D — Failure disposition](#5-class-d--failure-disposition)
6. [Class E — State and idempotency](#6-class-e--state-and-idempotency)
7. [Concurrency, timeouts, queues, and HTTP](#7-concurrency-timeouts-queues-and-http)
8. [Build, tests, and documentation](#8-build-tests-and-documentation)
9. [Quick scan](#9-quick-scan)

## 1. Scope and privacy

- Confirm only intended files and behaviors changed.
- Confirm no prior-client name, topology, endpoint, payload, identifier, schedule, volume, or
  incident detail entered source, comments, fixtures, logs, tests, or documentation.
- Confirm no secret, token, private hostname, tenant identifier, personal data, or production
  payload was added.
- Use synthetic, structurally minimal test data.
- Preserve unrelated user-authored changes and existing conventions.

## 2. Class A — Value contracts

- Pin `output` on multi-branch expressions, `targetValue` attributes, and string concatenations that
  mix typed variables so media-type inference cannot fail under concurrency.
- Confirm batch records, persistent queue payloads, and batch-step HTTP bodies use values that
  serialize on the target runtime (avoid map views / connector objects across batch steps; JSON is
  commonly appropriate for HTTP bodies inside `<batch:step>`).
- Remember `default` covers null and **absent** fields; present empty strings/collections need
  `isEmpty` / first-non-empty selection.
- Prefer already-known request identifiers over re-deriving from dual attribute/bean accessors;
  normalize at the system-facing boundary when that app owns the shape.
- Coerce types to what the target API accepts (for example Number vs String).
- Confirm MUnit fixtures match the worst-case production shape for the changed path.
- Validate query inputs; select every field downstream transforms consume. Escape or bind
  user-derived values with the connector's supported mechanism—presence checks alone do not prevent
  injection.
- Confirm empty results, null results, pagination (or single-page limits), and connector-specific
  result shapes are handled for the changed query path.
- Save the original message before scatter-gather when later steps need it.
- Unquoted DW identifiers start with a letter.
- Import `try` from `dw::Runtime` whenever the script calls `try()`.

## 3. Class B — Expression embedding

- For every changed CDATA block that starts with `#[`, confirm the expression ends with `]`
  **immediately before** the CDATA terminator `]]>` (three closing brackets before `>` when the
  script ends with `}`: `}]]]>` not `}]]>`).
- Do not assume sibling header/query/uri blocks prove the edited block is valid.
- Packaging success is not proof that `#[…]` evaluates; connector Map/MultiMap transform errors after
  markup edits are Class B until disproven.

Heuristic (repo-relative):

```bash
# Flag CDATA that opens an expression and may truncate it (review each hit)
rg -n '<!\[CDATA\[#\[' -g '*.xml' src || true
```

## 4. Class C — Contract authority

- Identify the **bound** contract on `apikit:config` (or equivalent): local file path **or**
  published Exchange/Maven pin. An unbound local copy is not runtime authority.
- For local-bound contracts, edit the bound file and flows; do not invent an Exchange publish unless
  the project already publishes that artifact.
- For published-bound contracts, update source of truth, bump/publish pin, repoint APIKit if needed,
  sync human-facing copies, and align consumers.
- Inventory routes both ways:
  - bound resource/method without flow → typically `APIKIT:NOT_IMPLEMENTED` / 501 + startup warnings
  - path absent from bound contract → typically `APIKIT:NOT_FOUND` / 404
  - path present, method missing → typically `APIKIT:METHOD_NOT_ALLOWED` / 405
  - implementing flow with no bound resource → dead path
- Verify methods, parameters, media types, status codes, and error envelopes against implementation.
- Confirm `flow-ref` targets and renames update tests, logs, alerts, and docs.

## 5. Class D — Failure disposition

- Confirm permanent vs retryable classification for new or changed error paths; do not retry typical
  permanent 4xx inside `until-successful`.
- Retry 401 only when each attempt can refresh credentials, tokens, or signatures; otherwise treat
  401 as permanent even if the operation is idempotent.
- For app-driven re-selection of the same business record (scheduler/poll eligible set): explicit
  disposition for permanent errors; use attempt budget + terminal state when bounded retry is
  required—do not force terminal exit on intentional indefinite retryable recovery. For queue/event
  listeners, prefer source-native redelivery/DLQ when already bounding retry.
- For `until-successful`, permanent errors must not retry; diagnostics must survive attempt reset
  (log in-attempt, durable capture, or nested cause)—not only vars that roll back on exhaustion.
  Regenerate per-attempt auth material when retrying auth-sensitive calls. Bound retries with
  backoff or jitter where appropriate so many records/replicas do not amplify dependency load.
- Multi-hop `<try>` (dependency then writeback): attribute the hop that failed; gate "success"
  messages on evidence the first hop completed.
- Structured error payloads use stable keys the consumer reads; logger `flowName` matches the
  enclosing flow.
- Business-impactful skips are not log-only: durable error, metric, or intentional disposition.
- `foreach` item isolation: `on-error-continue` when one item must not abort the rest. Do not equate
  that with batch steps—batch isolates failed records via job/step failure policy; `on-error-continue`
  on a batch step can hide failures.
- Parse error payloads defensively (`try` / read); avoid error-handler double faults.
- `on-error-continue` cannot discard work that still needs processing; queue delivery semantics
  verified before swallow.
- Never claim automatic reprocessing without source/queue evidence.

## 6. Class E — State and idempotency

- Object Store: non-null default or explicit `OS:KEY_NOT_FOUND` handling—never `#[null]` as default.
- OS keys are store-legal types (encode Binary hashes as hex/string). Optional cache degrades to
  source of record on store errors.
- Verify TTL, maxEntries, persistence, multi-replica, stale-data, and **atomicity** for changed
  stores—especially attempt counters or idempotency keys updated by overlapping schedulers/replicas
  (retrieve-modify-store can lose concurrent updates unless the design accounts for it).
- Polling/source connector defaults match sibling operations for the installed version when fields
  required downstream are at risk.
- Watermark/dedupe hold: document recovery if deploy does not re-emit failed ids.
- Content-hash projects: hashed fields still match the outbound transform. Adding a consumed field
  without hashing risks silent skip; removing a field from the transform but not the hash risks churn.
- Event listeners read the verified nested payload shape for this project.
- Continuous listeners use an appropriate reconnection strategy for the installed connector.
- Creates/upserts remain idempotent across retry and failed writeback where duplicates are possible.

## 7. Concurrency, timeouts, queues, and HTTP

- Effective concurrency accounts for consumers, `maxConcurrency`, parallel scopes, batch, replicas,
  pools, and dependency limits.
- Queue messages stay minimal and serializable.
- Timeout budget covers inner calls, retries, and error mapping with margin.
- Confirm idle timeout is not used as a substitute for response/read timeout on active requests
  (idle typically governs unused persistent connections).
- Connection pool bounds are deliberate and valid for the installed connector version.
- For GET, HEAD, or OPTIONS, rely on verified connector body behavior or set `sendBodyMode="NEVER"`
  when the project needs an explicit no-body guarantee.
- Correlation propagation verified when end-to-end tracing is claimed.

## 8. Build, tests, and documentation

- Run formatter/linter and focused MUnit for the changed path, then the required full build.
- Tests cover success and meaningful failure; fixtures can fail the real mechanism.
- Operational version metadata matches the packaged artifact when the project logs a version.
- Update owning docs, runbooks, recovery notes, `AGENTS.md` invariants, and changelog when behavior
  changed.
- Review the final diff for unsupported assumptions and unrelated edits.

## 9. Quick scan

| Priority | Check | Class |
| --- | --- | --- |
| High | No secrets or client-derived identity introduced | — |
| High | Embedded `#[…]` intact after CDATA/XML (Class B) | B |
| High | Bound contract (local file or published pin) and routes agree both ways (Class C) | C |
| High | Failures classified and attributed; permanent/poison bounded; retryable policy explicit; 401 gated (Class D) | D |
| High | Batch/queue serialization safe; no delivery loss | A/D |
| High | Retries and concurrency within proven dependency budget | D |
| Medium | Media types, empty vs null, dual accessors, fixture fidelity | A |
| Medium | OS miss/keys, source defaults, watermark recovery, hash parity | E |
| Medium | Timeout budget, minimal queues, correlation | — |
| Low | Names, imports, version strings, docs aligned | — |

## Project-local additions

Keep project-specific checks in the consuming repository, not in this reusable skill. Use neutral
mechanism-based wording if a local lesson is later promoted upstream.
