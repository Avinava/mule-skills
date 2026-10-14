# Mechanism signatures, deploy bursts, and memory pressure

## Contents

- [Recurring mechanism signatures](#recurring-mechanism-signatures)
- [Deploy-related bursts](#deploy-related-bursts)
- [Memory pressure](#memory-pressure)

Read this when the symptom resembles a known signature, lines up with a deployment window, or looks
like heap pressure. Signatures are hypothesis starters only.

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

Judge pressure by the old-generation pool rather than total heap: its peak against its limit, and
its baseline trend across days in hourly or daily buckets. Compare that with old-generation collection
count and time, payload size, concurrent work, batch settings, queue depth, CPU load, free host memory,
and replica divergence. A total-heap sawtooth is normally collection activity; frequent
old-generation collections that reclaim little suggest pressure, and a rising old-generation floor is
only a leak hypothesis until retention evidence supports it.

Check for:

- full-payload logging or repeated serialization
- large repeatable in-memory streams
- oversized variables or queue messages
- high batch or parallel concurrency
- unbounded caches or object-store usage
- connector or custom-code resource retention
