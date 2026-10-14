# JVM, thread, and pool diagnostics

## Contents

- [Read-only checks first](#read-only-checks-first)
- [What is available without a shell](#what-is-available-without-a-shell)
- [Reading a thread dump](#reading-a-thread-dump)
- [Blocked cpu-light patterns](#blocked-cpu-light-patterns)
- [Heap histogram method](#heap-histogram-method)
- [Connection-pool exhaustion signatures](#connection-pool-exhaustion-signatures)
- [502, 503, and 504 decision guide](#502-503-and-504-decision-guide)

Read this when requests wait, latency rises without an obvious dependency error, a replica looks
saturated, or memory pressure needs more than the old-generation trend in
[signatures-and-pressure.md](signatures-and-pressure.md). Everything here produces hypotheses until a
discriminating check separates the alternatives. Verify thread names, pool strategy, and diagnostic
availability against the installed runtime and deployment target before relying on any pattern.

## Read-only checks first

Order checks by cost and risk. Do not capture dumps or restart anything until cheaper evidence has
been read.

1. Logs and error grouping for the affected window, deduplicated by transaction.
2. Runtime metrics: CPU, old-generation pool, collection count and time, thread count, and replica
   divergence.
3. Source and configuration: listener, flow, pool, scheduler, and connector settings on the path.
4. Deployment and replica events near the first symptom.
5. Only then, a thread dump or histogram, taken from one affected replica, with the time recorded.

A dump is a snapshot. One dump shows what is stuck at that instant, not for how long. Take at least
two spaced apart before calling a thread "stuck", and label a single dump Observed for the instant
only.

## What is available without a shell

Managed platforms usually give no interactive shell on the replica, so shell-based runbooks that
assume local process tools do not apply.

- Confirm what the target offers: platform metrics, log download, and any supported diagnostic
  capture. Treat anything not confirmed as unavailable.
- When no dump capture exists, infer saturation from indirect signals: thread-count and CPU metrics,
  requests waiting in logs, pool-wait or timeout messages, and queue depth.
- Reproduce locally or in a lower environment when a dump is essential, and mark the result as a
  reproduction, not production evidence.
- State which evidence is missing because the platform cannot provide it, and name the next
  discriminating check that remains possible.
- Dumps and histograms can contain payload fragments and credentials. Treat them as sensitive, never
  paste raw contents into reusable output, and keep them out of the repository.

## Reading a thread dump

Group threads by pool before reading any single stack.

| Pool (name prefix varies by runtime) | Intended work | Healthy shape |
| --- | --- | --- |
| cpu-light | Non-blocking routing, short transforms, listener hand-off | Mostly idle or in brief runnable bursts |
| io | Blocking I/O, connector operations, waits on dependencies | Waiting threads are normal; watch for the whole pool waiting |
| cpu-intensive | Heavy transforms, parsing, computation | Runnable under load; a long run is a sizing or payload question |
| Combined or shared strategy | All of the above in one pool | Judge by stack content, not by pool name |
| Source, batch, and custom threads | Pollers, batch steps, schedulers | Depends on the source; match to the flow that owns them |

Reading method:

1. Count threads per pool and per state. A pool where nearly all threads share one state is the lead.
2. For each common state, group by the top application frame. Many threads parked at the same call
   site point at one shared bottleneck.
3. Identify the resource each blocked thread waits on: a lock, a pool checkout, a socket read, a
   queue, or a future. Name the holder when the dump shows it.
4. Look for lock cycles and a single thread holding a lock that many others wait on.
5. Map the call site back to the flow and connector in source before naming a cause.

Mule stacks are deep. Skim framework frames and anchor on the first frame that belongs to the
application, a connector, or a driver.

## Blocked cpu-light patterns

cpu-light threads must not block. Candidate patterns, each a hypothesis to confirm in source:

- A blocking connector call or synchronous wait reached on a cpu-light thread because of a
  processing-strategy or scope boundary.
- A custom component or script doing blocking work without moving off the cpu-light pool.
- A lock or synchronized section shared with slower work, so fast threads queue behind slow ones.
- A downstream wait inside a scope that keeps the calling thread until completion.

Signature in telemetry: listener requests wait while CPU is low, dependency latency looks normal, and
the dump shows the cpu-light pool occupied by threads at one blocking call site. Discriminating
check: confirm the call site's pool in source and configuration, then compare with a dump taken when
traffic is low.

## Heap histogram method

Use a class histogram when old-generation pressure is established and the retained type is unknown.

1. Establish pressure first from old-generation peak, floor trend, and collection time.
2. Take histograms at two or more points, spaced apart, from the same replica.
3. Compare growth by class, not absolute size. A type that grows between snapshots and does not
   shrink after collection is a retention lead.
4. Map the leading type to its source: payload buffers, parsed documents, cached objects, batch or
   queue records, or connector resources.
5. Cross-check with the checklist in `signatures-and-pressure.md` (payload logging, repeatable
   in-memory streams, oversized variables, concurrency, unbounded caches).

A histogram shows what exists, not who retains it. A retention path needs a heap dump and is rarely
available on a managed platform. Without it, leave the cause as Hypothesis and describe the
discriminating check.

## Connection-pool exhaustion signatures

Pools exhaust when checkout demand outlasts release. Signatures, all hypotheses until source and
telemetry align:

| Signature | Likely mechanism | Discriminating check |
| --- | --- | --- |
| Timeouts waiting for a connection, with dependency latency normal | Pool smaller than effective concurrency | Compare pool limit with effective concurrency across consumers, parallel scopes, and replicas |
| Pool wait errors that start after one slow dependency call | Connections held by slow calls, others queue | Check per-call duration around the first failure and any missing or generous timeout |
| Steady growth of open connections, no release | Leak: connection not closed on an error path | Look for error paths that skip release; check whether a stream is consumed before the scope ends |
| Failures only on some replicas | Per-replica pool or a stuck replica | Compare replica metrics and logs before changing configuration |
| Burst after a dependency recovers | Retry amplification | Check retry scope, backoff, and the total retry budget on the path |

Do not recommend a pool size without observed workload. Recommend the measurement that would justify
one.

## 502, 503, and 504 decision guide

Identify who produced the status before explaining it. A gateway, load balancer, proxy, or the
application itself can emit each one.

| Status | Typical meaning | First discriminating checks |
| --- | --- | --- |
| 502 | An upstream returned an invalid response or the connection broke | Did the application run? Check for replica restart, crash, or reset connections near the time |
| 503 | No healthy backend, or the application shed load | Replica count and readiness, startup or rolling transition, application back pressure |
| 504 | The intermediary timed out waiting on the application | Compare the intermediary deadline with the application and dependency budgets; find where time went |

Steps:

1. Find the layer that emitted the status from response headers, gateway logs, or application logs.
2. Check whether the application received the request. No application log entry for the transaction
   suggests the failure sits in front of it, but missing logs are inconclusive until retention and
   level are known.
3. Align with deployment and replica events. Transitions can cause 502 or 503 bursts, but timestamps
   alone do not prove it.
4. For 504, build the deadline stack: intermediary, listener, flow, retries, dependency. The shortest
   deadline that elapsed first is the lead, and a caller-side timeout never names the origin.
5. Keep the cause unresolved until one check separates a front-layer fault from an application one.
