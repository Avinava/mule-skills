# Review domains

## Contents

1. [Evidence routing](#evidence-routing)
2. [Mode coverage](#mode-coverage)
3. [Contracts and boundaries](#contracts-and-boundaries)
4. [Flows and DataWeave](#flows-and-dataweave)
5. [Errors and delivery](#errors-and-delivery)
6. [Concurrency, latency, and state](#concurrency-latency-and-state)
7. [Security, configuration, and logging](#security-configuration-and-logging)
8. [Tests, build, and deployment](#tests-build-and-deployment)
9. [Documentation and operations](#documentation-and-operations)

## Evidence routing

Use the evidence that owns each question and cross-check important behavior:

| Question | Primary evidence | Cross-check |
| --- | --- | --- |
| What changed? | Git diff or selected revision | Callers, references, tests, docs |
| What runs? | Mule XML and DataWeave | MUnit and runtime evidence |
| What is promised? | RAML/OAS or event schema | Listeners, APIKit routes, mappings |
| What fails or continues? | Local/global error handlers | Response transforms, retries, tests |
| What is configured? | Property references and templates | Deployment inputs; never values |
| What is operationally true? | Current telemetry | Source, configuration, deployment state |
| Why does the system exist? | Verified prose or provided context | Runtime boundary; do not infer from names |

Treat user-provided context as intent, not runtime proof. Treat existing prose as contextual evidence
until verified. Record specification/implementation mismatches as findings when they create risk.

## Mode coverage

### Change review

Start with the diff, then follow impact edges. Review:

- changed flow and every referenced or calling flow affected by its contract
- changed transform inputs, outputs, and every downstream field consumer
- changed endpoint/event contract and implementation in both directions
- changed configuration keys, defaults, deployment inputs, and environment templates
- changed error, retry, queue, batch, timeout, concurrency, state, and logging behavior
- affected tests, documentation, runbooks, dashboards, and release notes

Do not expand into an unrelated repository audit. Report nearby pre-existing issues only when they
make the changed behavior unsafe or prevent a correct assessment, and label them as pre-existing.
For Mule-focused tooling, parsers, linters, build extensions, or deliberately partial fixtures,
review the changed Mule semantics and the harness that exercises them. Do not require a fixture to
be independently deployable unless the repository or user presents it as a release unit.

### Project review

Inventory the whole repository and cover every section below. Use flow reachability and public
contracts to prioritize deep inspection. Do not equate file counts or lint volume with project
health. State sampling or unreviewed areas explicitly.

### Release readiness

Perform project coverage plus these gates:

- release candidate and intended version are unambiguous
- required lint, security, test, and package steps pass
- packaged runtime and connector compatibility match the deployment target
- public contract changes are compatible or coordinated
- configuration inputs, secret boundaries, and deployment automation are complete
- changed asynchronous paths have safe acknowledgement, retry, idempotency, and recovery behavior
- required documentation, operations guidance, rollback, and verification signals are current

Do not perform version changes, commits, tags, publishing, deployment, or approvals.

## Contracts and boundaries

Apply Classes A–E and the mandatory **cross-cutting** gates from `mule-development`, including the
following **contract authority and reachability** mechanisms (Class C):

- Identify the **bound** contract on APIKit configuration: a local resource path **or** a published
  Exchange/Maven pin. Do not treat an unbound or drifted file as runtime authority.
- Require Exchange publish/bump steps only when the project already binds a published contract
  artifact; local-bound `api="*.raml"` projects edit the bound file without inventing a publish path.
- Inventory routes both ways:
  - bound resource/method without implementation → typically `APIKIT:NOT_IMPLEMENTED` / 501 and
    startup missing-implementation warnings
  - path absent from bound contract → typically `APIKIT:NOT_FOUND` / 404
  - path present, method not allowed → typically `APIKIT:METHOD_NOT_ALLOWED` / 405
  - implementation with no bound resource → not APIKit-routable; inspect sources and `flow-ref`
    callers before concluding it is unreachable
  - renames incomplete across contract, pin, local copy, and consumers
- Compare resources, methods, parameters, headers, security, media types, schemas, examples, status
  codes, and error envelopes with listeners and APIKit routes.
- For events, identify the authoritative schema/version and verify publisher/consumer mappings in
  both directions; do not force APIKit checks onto non-API projects.
- For events and queues, verify payload schema, acknowledgement, ordering, retry, deduplication, and
  side effects instead of forcing an HTTP model.
- Detect removed or renamed routes, required fields, incompatible type changes, new validation,
  changed defaults, and response-shape drift.
- Verify correlation behavior and trust boundaries without exposing private hostnames or identity.
- Distinguish an intentional internal contract from a public or consumer-facing one using evidence.

## Flows and DataWeave

Apply **value contracts** and **expression embedding** mechanisms (Classes A and B):

- Trace success, alternate, empty-input, and terminal error paths through `flow-ref` edges.
- Check that source-less flows and subflows use the intended error strategy and do not assume an
  implicit transaction boundary.
- Verify DataWeave selectors, null vs empty handling (`default` covers null and absent fields;
  present empty strings need `isEmpty`), dual attribute/bean accessors, typed coercions, imports,
  media types, field mappings, and output shapes against actual inputs and downstream consumers.
- Require explicit `output` when mixed input media types, inference mismatch, or the next consumer's
  writer contract makes it necessary; do not require it mechanically for every branch.
- Distinguish optional defaults from required-data validation; do not silently null invalid required
  values to avoid an exception.
- Prefer already-known request identifiers over re-deriving ambiguous response ids when evidence
  shows dual or empty representations.
- Check scatter-gather route indexes and preservation of message state when later processors need it.
- Verify batch records and persistent queue messages contain supported serializable values; avoid
  lazy iterators, streams, map views, or connector-specific objects across serialization boundaries.
- For changed CDATA `#[…]` in query-params, headers, or uri-params, verify the expression still ends
  with `]` before `]]>` (packaging success is not evaluation proof; Map/MultiMap transform failures
  after markup edits are Class B until disproven).
- Check query inputs, escaping or binding, pagination, empty results, and selection of all fields
  consumed downstream.
- Treat naming and decomposition as improvements unless they cause broken references, misleading
  operations, or unsafe behavior.

## Errors and delivery

Apply **failure disposition** mechanisms (Class D):

- Verify the effective local or global handler and the caller/source outcome for every meaningful
  failure path.
- Check defensive access to optional or binary error payloads and prevent error-handler double faults.
- Distinguish propagate, continue, retry, fallback, acknowledgement, redelivery, dead-letter, and
  terminal loss behavior.
- Before accepting `on-error-continue`, verify it cannot acknowledge or discard work that still
  requires processing.
- Verify permanent vs retryable classification; retries are limited to appropriate errors, safe for
  idempotency, and fit the caller/dependency budget. Flag retry of **permanent, poison, or
  unclassified** errors on app-driven re-selection. For intentional indefinite retry of classified
  retryable failures, require backoff, monitoring, escalation/ownership, recovery criteria, and a
  replay/manual-recovery path. Require an attempt/deadline budget and exhaustion disposition only
  when the project claims a bounded policy. For listeners, verify source redelivery/DLQ before
  requiring app counters.
- Inside `until-successful` or equivalent, permanent client errors should not be retried without a
  documented reason. Diagnostics must survive attempt reset (in-attempt log, durable capture, or
  nested cause)—ordinary vars may roll back before the outer `RETRY_EXHAUSTED` handler. Retry 401
  only when each attempt can refresh credentials, tokens, or signatures. For selective retry, catch
  permanent types inside the scope as a classified result and let retryable types escape.
- Multi-hop try scopes must attribute the failing hop; success messages require evidence the first
  hop completed.
- Business-impactful skip guards need a durable error, metric, or intentional disposition—not log
  only.
- Group connector failure, retry summary, structured logger, and default exception-listener entries
  when they describe the same transaction.
- Do not claim automatic reprocessing or recovery without source and queue evidence.

## Concurrency, latency, and state

Apply **state and idempotency** mechanisms (Class E) alongside concurrency and latency:

- Calculate effective concurrency from source consumers, flow limits, batch-job concurrency,
  parallel scopes, replicas, pools, and dependency quotas.
- Treat batch block size as a memory and scheduling parameter, not a direct count of simultaneous
  dependency requests.
- Distinguish connect, response, read, connection-idle, proxy, retry, and total caller deadlines.
- For synchronous paths, verify inner calls, retries, and error mapping fit inside the upstream
  deadline with margin. Treat connection idle timeout as unused-connection lifetime, not as the
  active request response/read deadline.
- Check back pressure, ordering, race conditions, shared state, duplicate delivery, and overlapping
  scheduler or batch instances.
- For Object Store, verify missing-key behavior and non-null defaults (never `#[null]` as default).
  Treat only an evidenced `OS:KEY_NOT_FOUND` as an expected miss; an optional cache may degrade on
  availability failures such as `OS:STORE_NOT_AVAILABLE`, while invalid keys, null values,
  configuration/security errors, and programming defects remain visible. Verify store-legal String
  keys (encode Binary hashes), TTL, persistence, multi-replica access, atomicity, sensitive-data
  exclusion, and stale-data behavior.
- When content hashes or skip-lists exist, verify hashed fields match the outbound transform: missing
  hash fields for new consumed inputs risk silent skip; hash fields left after transform removal risk
  unnecessary churn.
- Check polling/source defaults against sibling operations when downstream ids or body fields are
  required; note watermark/dedupe hold and recovery when deploy does not re-emit failed records.
- Verify event listener payload nesting against the project's verified shape and reconnection policy
  for continuous streams.
- Prefer idempotent create/upsert patterns where failed writebacks can duplicate work.
- Require current workload and dependency evidence before recommending numeric tuning values.

## Security, configuration, and logging

- Apply the security/configuration and privacy/observability cross-cutting gates even when no A–E
  mechanism appears to be the primary changed behavior.
- Review authentication and authorization boundaries, TLS, secure properties, policy assumptions,
  input validation, and least-privilege behavior at the mechanism level.
- Never open or reproduce secret values, secure-property ciphertext, certificates, private keys, or
  production payloads.
- Verify property keys exist in the expected templates and classify required/defaulted status only
  when evidence proves it.
- Detect hard-coded credentials, private endpoints, tenant identifiers, and environment-specific
  identity in reusable source or documentation.
- Check logs for full payloads, secrets, personal data, unsafe identifiers, incorrect flow names,
  structured error-key mismatches against consumers, duplicate failures, and missing safe correlation
  or outcome fields.
- Treat log absence as inconclusive when retention, level, sampling, or error handling can hide an event.

## Tests, build, and deployment

- Apply the validation/documentation and capacity/lifecycle cross-cutting gates.
- Map tests to changed and critical behavior: success, alternate branches, transformations,
  connector errors, retries, error handlers, batch/queue semantics, and contract mapping.
- Evaluate assertions and mocks, not only test count. Detect tests that cannot fail for the changed
  behavior, that mock away the mechanism under review, or that encode a more convenient shape than
  production (fixture fidelity).
- Packaging success does not prove CDATA expressions evaluate or that the bound contract matches
  routes.
- Follow repository-required lint, security, test, and package commands. Do not weaken them to obtain
  a passing result.
- Run the development skill's embedded-expression checker when Mule XML changes.
- Verify POM, Mule artifact metadata, Java, connector, plugin, and deployment-target compatibility.
- Check artifact version surfaces (including logger/app version properties), deployment inputs,
  rollback path, and current-vs-desired version interpretation when relevant.
- Treat deployment overlap as a hypothesis until lifecycle, replica, or before/after evidence supports it.

## Documentation and operations

- Apply the delivery/transactions cross-cutting gate to asynchronous and stateful paths.
- Confirm architecture, contract, onboarding, configuration, operations, and flow documentation
  remain consistent with reviewed behavior.
- Check that operational guidance covers schedulers, batches, queues, retries, health signals,
  correlation, recovery, and known gaps when applicable.
- Separate current behavior from recommendations and stakeholder-provided context.
- Verify links, Mermaid syntax, source paths, and privacy using the documentation skill when installed.
- Require useful monitoring and verification signals for critical or asynchronous behavior, but do
  not invent an observability stack that the repository does not evidence.
