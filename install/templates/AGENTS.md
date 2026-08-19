# <!-- PROJECT_NAME --> — Project Guide

> Generate this file from current repository evidence. Remove every unused section and unresolved
> placeholder. Do not copy identity, topology, examples, or operating values from another project.

<!-- SKILLS_LOCATION -->

## Purpose and boundary

<!-- Describe the business capability, intended users, application role, deployment target, and
system boundary. Attribute user-provided business context and keep runtime claims evidence-backed. -->

This Mule 4 application <!-- DESCRIPTION -->.

## Source map

<!-- Replace this example with the actual repository structure. -->

| Path | Responsibility |
| --- | --- |
| `pom.xml` | Build and dependency metadata |
| `mule-artifact.json` | Mule runtime compatibility |
| `src/main/mule/` | Mule configuration and flows |
| `src/main/resources/` | Contracts, DataWeave, and configuration templates |
| `src/test/` | MUnit tests and fixtures |

## Runtime paths

| Trigger or endpoint | Owning flow | Main collaborators | Outcome |
| --- | --- | --- | --- |
| <!-- Trigger --> | <!-- Flow --> | <!-- Flows/systems --> | <!-- Result --> |

Document synchronous responses, asynchronous acknowledgement, retry, error, and recovery paths
when they differ.

## Architecture and delivery semantics

<!-- Include only patterns proven by source or explicitly provided by project stakeholders. -->

- **Application role:** <!-- entry API, orchestration, system-facing API, worker, scheduler, other -->
- **Dependencies:** <!-- role-based summary with links to owning docs -->
- **Error strategy:** <!-- local/global handlers and observable caller/source outcome -->
- **Queues/events:** <!-- acknowledgement, persistence, ordering, redelivery, idempotency -->
- **Correlation:** <!-- inbound adoption and outbound propagation -->
- **Security boundary:** <!-- mechanism and property keys; never values -->

## Configuration

Document property keys without values:

| Key | Purpose | Source | Required/defaulted evidence |
| --- | --- | --- | --- |
| <!-- property.key --> | <!-- Purpose --> | <!-- Relative path --> | <!-- Status --> |

Never include secrets, ciphertext, private hosts, tenant identifiers, personal data, or local
machine paths.

## Concurrency, timeouts, and state

<!-- Keep values only when verified in this repository. -->

| Boundary | Current behavior | Constraint or rationale | Evidence |
| --- | --- | --- | --- |
| <!-- Flow/queue/batch/call --> | <!-- Consumers/concurrency/timeouts/state --> | <!-- Why --> | <!-- Path --> |

Distinguish connect, response, read, connection-idle, retry, proxy, and total upstream deadlines.
Calculate concurrency across sources, flows, batch jobs, parallel scopes, replicas, pools, and
dependency capacity.

## Conditional invariants

Record only invariants actually used by this project. Prefer mechanism language from
`mule-development` Classes A–E and its mandatory cross-cutting gates. Examples include:

- a content hash must change when its documented source fields change (hash fields == outbound DWL);
- a cache miss must follow a specific source-of-record path; optional cache degrades only on
  classified availability failures, while invalid keys/configuration remain visible;
- app-driven re-selection classifies permanent vs retryable errors; bounded policies use an attempt
  budget and terminal state; intentional indefinite retry of only retryable failures is documented;
  queue/event paths document source redelivery/DLQ when used;
- the bound API contract (local file or published pin) is the routing authority; copies stay in sync;
- event listeners read a verified nested payload shape (document the path used in this project);
- an event or create path remains idempotent across redelivery and failed writeback;
- a public contract change requires coordinated consumer updates;
- required security/configuration, capacity/lifecycle, delivery/transaction, privacy/observability,
  and validation gates are documented for each critical path.

| Invariant | Owning source | Affected files | Required validation |
| --- | --- | --- | --- |
| <!-- Rule --> | <!-- Evidence --> | <!-- Paths --> | <!-- Test/check --> |

## Build, test, and deploy

Use only commands verified in this repository:

| Action | Command or tool | Notes |
| --- | --- | --- |
| Validate | <!-- Command --> | <!-- Scope --> |
| Test | <!-- Command --> | <!-- Expected suites --> |
| Package | <!-- Command --> | <!-- Artifact path pattern --> |
| Deploy | <!-- Workflow/tool --> | <!-- Environment inputs, no values --> |

Do not assume configuration is deployed separately, tests should be skipped, or a build implies a
release. Use `mule-testing` for MUnit authoring and repair, and `mule-build` for test execution,
validation, packaging, and explicitly requested release actions. Use the repository's release
policy.

## Operational checks

| Signal | Healthy evidence | Investigation path |
| --- | --- | --- |
| <!-- Scheduler/API/queue/batch --> | <!-- Completion/latency/outcome --> | <!-- Log/metric/flow --> |

Record actual telemetry coverage before comparing applications. Treat deploy overlap, missing error
logs, retry summaries, and memory sawtooth patterns as signals rather than proof of root cause.
Use the `mule-ops` skill for runtime health analysis and `mule-troubleshooting` when a causal
diagnosis is required.

## Development guardrails

- Use `mule-api-design` for consumer-facing HTTP design and RAML/OAS authoring. Keep one contract
  source of truth, validate it locally, and separately approve Design Center sync and publication.
- Use the `mule-development` skill and complete its post-development checklist for source changes (Classes A–E: value contracts, expression embedding, contract authority, failure
  disposition, state/idempotency; plus applicable cross-cutting gates).
- Use `mule-testing` for behavior-focused MUnit tests, faithful events and fixtures, boundary mocks,
  observable assertions, and test-only build configuration.
- Validate query inputs and select every field consumed downstream.
- Keep batch records and queue messages minimal and serializable; pin media types for the next
  consumer.
- Verify Object Store miss/failure classification; a `null` default still raises `OS:KEY_NOT_FOUND`,
  and invalid key/configuration errors are not cache misses.
- Verify effective local or global error handling, permanent vs retryable classification, and the
  final caller/source outcome.
- Preserve correlation without logging raw payloads or sensitive identifiers.
- Verify deployment-target support, transaction/delivery behavior, streaming/memory, and security
  configuration when the changed path uses them.
- Update contracts (bound local file or published version), tests, operations guidance, and
  documentation when behavior changes.

## Known gaps and decisions

| State | Item | Evidence or next check |
| --- | --- | --- |
| <!-- Verified/Inferred/Provided/Unresolved/Recommended --> | <!-- Item --> | <!-- Source/action --> |

## Documentation

Use the `mule-docs` skill for evidence-backed documentation creation and targeted refreshes. Link the current documentation set here:

- <!-- Documentation path — Description -->

## Review

Use the `mule-review` skill for change, PR, whole-project, and release-readiness reviews. Reviews report evidence-backed findings and remediation options without
modifying source or PR state unless explicitly requested.
