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

- Compare RAML/OAS resources, methods, parameters, headers, security, media types, schemas, examples,
  status codes, and error envelopes with listeners and APIKit routes.
- For events and queues, verify payload schema, acknowledgement, ordering, retry, deduplication, and
  side effects instead of forcing an HTTP model.
- Detect removed or renamed routes, required fields, incompatible type changes, new validation,
  changed defaults, and response-shape drift.
- Verify correlation behavior and trust boundaries without exposing private hostnames or identity.
- Distinguish an intentional internal contract from a public or consumer-facing one using evidence.

## Flows and DataWeave

- Trace success, alternate, empty-input, and terminal error paths through `flow-ref` edges.
- Check that source-less flows and subflows use the intended error strategy and do not assume an
  implicit transaction boundary.
- Verify DataWeave selectors, defaults, coercions, imports, media types, field mappings, and output
  shapes against actual inputs and downstream consumers.
- Check scatter-gather route indexes and preservation of message state when later processors need it.
- Verify batch records and persistent queue messages contain supported serializable values; avoid
  lazy iterators, streams, map views, or connector-specific objects across serialization boundaries.
- Check query inputs, escaping or binding, pagination, empty results, and selection of all fields
  consumed downstream.
- Treat naming and decomposition as improvements unless they cause broken references, misleading
  operations, or unsafe behavior.

## Errors and delivery

- Verify the effective local or global handler and the caller/source outcome for every meaningful
  failure path.
- Check defensive access to optional or binary error payloads and prevent error-handler double faults.
- Distinguish propagate, continue, retry, fallback, acknowledgement, redelivery, dead-letter, and
  terminal loss behavior.
- Before accepting `on-error-continue`, verify it cannot acknowledge or discard work that still
  requires processing.
- Verify retries are bounded, limited to appropriate errors, and safe for idempotency.
- Group connector failure, retry summary, structured logger, and default exception-listener entries
  when they describe the same transaction.
- Do not claim automatic reprocessing or recovery without source and queue evidence.

## Concurrency, latency, and state

- Calculate effective concurrency from source consumers, flow limits, batch-job concurrency,
  parallel scopes, replicas, pools, and dependency quotas.
- Treat batch block size as a memory and scheduling parameter, not a direct count of simultaneous
  dependency requests.
- Distinguish connect, response, read, connection-idle, proxy, retry, and total caller deadlines.
- For synchronous paths, verify inner calls, retries, and error mapping fit inside the upstream
  deadline with margin.
- Check back pressure, ordering, race conditions, shared state, duplicate delivery, and overlapping
  scheduler or batch instances.
- For Object Store, verify missing-key behavior, non-null defaults, TTL, persistence, multi-replica
  access, atomicity, and stale-data behavior.
- Require current workload and dependency evidence before recommending numeric tuning values.

## Security, configuration, and logging

- Review authentication and authorization boundaries, TLS, secure properties, policy assumptions,
  input validation, and least-privilege behavior at the mechanism level.
- Never open or reproduce secret values, secure-property ciphertext, certificates, private keys, or
  production payloads.
- Verify property keys exist in the expected templates and classify required/defaulted status only
  when evidence proves it.
- Detect hard-coded credentials, private endpoints, tenant identifiers, and environment-specific
  identity in reusable source or documentation.
- Check logs for full payloads, secrets, personal data, unsafe identifiers, incorrect flow names,
  duplicate failures, and missing safe correlation or outcome fields.
- Treat log absence as inconclusive when retention, level, sampling, or error handling can hide an event.

## Tests, build, and deployment

- Map tests to changed and critical behavior: success, alternate branches, transformations,
  connector errors, retries, error handlers, batch/queue semantics, and contract mapping.
- Evaluate assertions and mocks, not only test count. Detect tests that cannot fail for the changed
  behavior or that mock away the mechanism under review.
- Follow repository-required lint, security, test, and package commands. Do not weaken them to obtain
  a passing result.
- Verify POM, Mule artifact metadata, Java, connector, plugin, and deployment-target compatibility.
- Check artifact version surfaces, deployment inputs, rollback path, and current-vs-desired version
  interpretation when relevant.
- Treat deployment overlap as a hypothesis until lifecycle, replica, or before/after evidence supports it.

## Documentation and operations

- Confirm architecture, contract, onboarding, configuration, operations, and flow documentation
  remain consistent with reviewed behavior.
- Check that operational guidance covers schedulers, batches, queues, retries, health signals,
  correlation, recovery, and known gaps when applicable.
- Separate current behavior from recommendations and stakeholder-provided context.
- Verify links, Mermaid syntax, source paths, and privacy using the documentation skill when installed.
- Require useful monitoring and verification signals for critical or asynchronous behavior, but do
  not invent an observability stack that the repository does not evidence.
