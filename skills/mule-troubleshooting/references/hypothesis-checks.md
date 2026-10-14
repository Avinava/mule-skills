# Hypothesis checks: timeouts, concurrency, and error propagation

## Contents

- [Timeout and connection failures](#timeout-and-connection-failures)
- [Concurrency and rate limits](#concurrency-and-rate-limits)
- [Error propagation and proxy behavior](#error-propagation-and-proxy-behavior)

Read this when a symptom involves a timer, a pool, throttling, or a caller-side 5xx whose origin is
unclear. Confirm each hypothesis with code and aligned telemetry before treating it as a cause.

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
