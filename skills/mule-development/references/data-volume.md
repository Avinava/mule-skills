# Data volume, streaming, and batch design

Use this reference when a flow handles large payloads, long record lists, bulk loads, or work that
must survive partial failure. It deepens the Capacity and lifecycle gate in
[Invariant classes and cross-cutting gates](invariant-classes.md#cross-cutting-gates); read Class D
there when record failures need a terminal outcome, and
[DataWeave design guidance](dataweave.md) when the transformation itself must stream.

## Contents

1. [Classify the payload first](#classify-the-payload-first)
2. [Repeatable and non-repeatable streams](#repeatable-and-non-repeatable-streams)
3. [When a stream is consumed](#when-a-stream-is-consumed)
4. [Heap budget method](#heap-budget-method)
5. [Large file pattern](#large-file-pattern)
6. [Batch, foreach, and parallel foreach](#batch-foreach-and-parallel-foreach)
7. [Block size, aggregators, and failure policy](#block-size-aggregators-and-failure-policy)
8. [Reconciliation and partial failure reporting](#reconciliation-and-partial-failure-reporting)
9. [Bulk job orchestration](#bulk-job-orchestration)
10. [Verify against installed runtime and connector versions](#verify-against-installed-runtime-and-connector-versions)

## Classify the payload first

Decide the shape of the data before choosing a mechanism. Record the answers in the handoff.

| Question | Why it decides the design |
|---|---|
| Is the payload a single value, a bounded collection, or an unbounded or very large sequence? | Bounded values can be held in memory; large sequences need streaming or chunking |
| Does the consumer read it once or many times? | Many reads need a repeatable source or deliberate materialization |
| Must records succeed or fail independently? | Independent records point to batch semantics; all or nothing points to a transaction or a single unit |
| Is order significant? | Parallelism and block processing can reorder work |
| Where does the data come from and go to? | The reader, the writer, and the connector decide what streaming is possible |

## Repeatable and non-repeatable streams

A stream strategy decides what happens when the same payload is read more than once.

| Strategy kind | Behavior | Choose when |
|---|---|---|
| Repeatable in memory | Buffers up to a configured limit, then fails or spills depending on version | Payloads are small and bounded by evidence |
| Repeatable file backed | Buffers in memory, then spills to disk | Payloads vary in size and several reads are needed |
| Non-repeatable | One forward pass; later reads see nothing or fail | One consumer reads the data once, and memory must stay flat |

- Configure the strategy per source or connector operation, and state why for each.
- A repeatable strategy trades memory or disk for safety. A non-repeatable one trades safety for
  flat memory. Pick on the access pattern, not on habit.
- Disk spill needs writable local storage and a cleanup story; check the deployment target.
- Treat buffer sizes as workload decisions. Take them from measured payload sizes, not from another
  project.

## When a stream is consumed

Anything that reads the payload can consume a non-repeatable stream.

- A logger that prints the payload, a transformer that selects from it, a `sizeOf`, a second
  transformer, or a debugger inspection can each exhaust or materialize it.
- Reading the payload into a variable keeps a reference; with a non-repeatable source the variable
  may hold an already consumed stream.
- An error handler that logs or republishes the payload may find it empty or truncated.
- Retries and redelivery re-run the flow; confirm the source provides a fresh stream each time.

Design the flow so exactly one component owns the read, and everything else works from metadata
(size, name, correlation id) captured before or alongside it. If several consumers are needed,
either use a repeatable strategy deliberately or fan out from a stage that materializes once.

## Heap budget method

Estimate memory as a method, using measured inputs from the target workload.

1. Measure the largest realistic payload and the typical payload.
2. Count concurrent in-flight units: listener or source concurrency, scheduler threads, parallel
   foreach branches, and batch workers.
3. Count copies. One payload can exist as raw bytes, a parsed structure, a transformed structure,
   and a serialized output at the same time. Transformations that cannot stream multiply the cost.
4. Multiply payload size by copies by concurrency, then add the fixed overhead of the application
   (libraries, caches, connection pools).
5. Compare against the heap actually available to the application on its deployment target, and
   leave headroom for garbage collection behavior.
6. Validate with a load run and the memory signals in the runtime, not by calculation alone.

If the estimate does not fit, reduce a factor: stream instead of materializing, lower concurrency,
chunk the work, or move the data through a file or external store. Do not paste a heap number or
buffer size from another project; record the inputs you used so the next engineer can redo the
estimate.

## Large file pattern

For files too large to hold comfortably, move bytes without materializing structure.

- Read with a streaming reader and process in one pass. Keep transformations forward only, as in
  [DataWeave design guidance](dataweave.md#streaming-and-one-pass-reads).
- Write results as a stream to the target, or to a staging location, then publish atomically
  (rename, manifest, or completion marker) so consumers never see a half written file.
- Track progress with a durable marker (offset, record count, or processed file name) so a restart
  resumes or safely repeats. See Class E for watermark and replay rules.
- Handle partial files: decide whether a failure midway discards output, quarantines the input, or
  resumes. Name the terminal outcome for the file, as Class D requires.
- Close streams on every path, including error paths, so file handles and connections do not leak.
- For remote file transports, confirm the connector's behavior for in-progress writes (files still
  being written by the sender) before processing.

## Batch, foreach, and parallel foreach

| Mechanism | Strength | Cost or risk | Choose when |
|---|---|---|---|
| Batch job | Per-record failure isolation, staged processing, aggregation, on-complete summary | Persists queues and records, adds scheduling overhead, asynchronous from the caller | Large record sets where records succeed or fail independently |
| `foreach` | Simple, sequential, preserves order, runs inside the caller's flow | One failing element fails the loop unless handled; no isolation | Small bounded collections, ordered processing, caller needs the result |
| Parallel `foreach` | Concurrency across elements | Ordering lost, error aggregation behavior differs, memory scales with parallelism | Independent elements, a bounded concurrency limit, and a defined way to collect failures |
| Scatter-gather or async scope | Fan out heterogeneous work | Failure and timeout semantics per route | A fixed small set of different operations |

- Pick batch when per-record outcomes matter after the caller has been answered. Pick `foreach`
  when the caller needs a synchronous answer about the whole collection.
- A flow that returns to its caller before batch finishes cannot report batch failures in that
  response. Define how the outcome is reported later (status endpoint, event, report).
- Parallel work needs an explicit concurrency bound tied to the downstream system's capacity, not
  to what the runtime allows.
- State what happens to a collection that fails midway through a `foreach`: abort, skip the
  element, or collect and continue. Class D owns the terminal outcome.

## Block size, aggregators, and failure policy

Batch settings are scheduling and memory decisions, not tuning folklore.

- **Block size** controls how many records a worker holds and processes together. Larger blocks
  raise memory per worker and reduce scheduling overhead; smaller blocks do the opposite. Decide
  from record size, worker count, and the heap method above, then confirm under load.
- **Aggregators** commit a group of records together. Their size defines the unit of downstream
  work and of failure: if the commit fails, the whole group is affected. Match the size to the
  downstream system's bulk limits and to the blast radius you accept.
- **Record failure policy** (how many failures are tolerated before the job stops, and whether
  failed records continue to later steps) is a business decision. State it explicitly rather than
  accepting a default. A policy that tolerates unlimited failures can hide a systemic fault; a
  policy that stops on the first failure can lose a whole run to one bad record.
- Handle failures per step: which step failed, whether failed records are accepted for later steps
  or only for a dedicated failure step, and where failed record details go.
- Keep per-record work idempotent. Batch can retry, resume, or reprocess records after a restart.
  See Class E.
- Do not use `on-error-continue` to quiet record failures without recording them; it can hide
  failed records from the summary.

## Reconciliation and partial failure reporting

A batch or loop that can partially fail needs a result nobody has to reconstruct from logs.

- In the on-complete phase, report totals: received, processed, failed, skipped, and any records
  left in an unknown state. Check that the numbers add up to the input count.
- Persist failed record identifiers and reasons (without sensitive field values) to a place an
  operator can act on: a dead-letter queue, a failure table, or a report file.
- For a synchronous API that handles a collection, return per-item outcomes. A multi-status
  response (HTTP 207 style) with an item level status and error reference lets a client retry only
  what failed. Never return plain success when some items failed.
- Distinguish retryable failures (transient downstream conditions) from terminal ones (validation
  failures) in the report, so replay does not repeat the unfixable.
- Design replay: failed items must be replayable without duplicating successful ones. That needs a
  stable item key and idempotent writes.
- Alert on the summary, not only on exceptions: a run that completes with failures is still an
  incident for the owner.

## Bulk job orchestration

Some systems expose an asynchronous bulk interface: submit a job, poll or subscribe for status,
then fetch results.

- Model the job as explicit states with a durable record: submitted, running, succeeded,
  partially failed, failed, abandoned. Persist the job identifier before relying on it.
- Split input to fit the target's per-job and per-request limits; take those limits from the
  target's current documentation, not from memory.
- Poll with a bounded interval and a stop condition (timeout, maximum attempts, terminal state).
  Prefer event or callback notification when the target supports it.
- Fetch and reconcile results per record, including failed record details, and feed failures into
  the reporting above.
- Make submission idempotent where possible (a client supplied key or a check for an existing
  job), so a restart does not create duplicate jobs.
- Define cancellation and cleanup: what happens to an in-flight job when the app stops or the
  deployment is replaced.
- Respect the target's concurrency and rate limits; apply back pressure upstream instead of
  queueing without bound.

## Verify against installed runtime and connector versions

Streaming strategies, batch options, and bulk connector behavior vary by runtime and connector
version. Before relying on a setting, a default, or a limit:

1. Read the runtime, connector, and plugin versions from the project. If a newer or compatible
   release is in question, use [the mule-dependencies skill](../../mule-dependencies/SKILL.md) for
   version and compatibility lookups.
2. Check the installed version's reference for stream strategy options, batch step and aggregator
   behavior, and the connector's bulk limits.
3. Confirm with a representative large input and a representative failure, not an assumption.
4. Record any difference from this guidance in the handoff, and follow the installed version.
