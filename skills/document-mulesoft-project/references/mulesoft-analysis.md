# MuleSoft analysis

## Contents

1. [Recognition and discovery](#recognition-and-discovery)
2. [Source-of-truth map](#source-of-truth-map)
3. [Flow analysis](#flow-analysis)
4. [Contracts and transformations](#contracts-and-transformations)
5. [Configuration and deployment](#configuration-and-deployment)
6. [Testing and operational behavior](#testing-and-operational-behavior)
7. [Common interpretation traps](#common-interpretation-traps)

## Recognition and discovery

Treat a repository as a Mule project when the evidence includes a Mule application descriptor or
Mule source tree plus compatible Maven metadata. Strong indicators are:

- `mule-artifact.json`
- `src/main/mule/`
- `<packaging>mule-application</packaging>`
- Mule runtime or Mule Maven plugin properties in `pom.xml`

Do not classify a repository from its name or README alone.

Search in this order:

1. Repository instructions and existing documentation.
2. POM and Mule artifact metadata.
3. Mule XML global configuration, listeners, flows, and subflows.
4. RAML/OAS and APIKit bindings.
5. DataWeave modules, transforms, and lookup data.
6. Configuration templates and property references.
7. MUnit, CI, and deployment files.

Ignore dependency caches, `target/`, generated catalog files, `.git/`, `.idea/`, `.vscode/`,
macOS metadata, logs, and binary credentials. Do not treat copied build artifacts as source.

## Source-of-truth map

| Question                  | Primary evidence                            | Cross-check                              |
| ------------------------- | ------------------------------------------- | ---------------------------------------- |
| What starts processing?   | Flow source element                         | API spec, scheduler config, queue config |
| What happens in order?    | Direct flow processors and referenced flows | DataWeave and connector operations       |
| What is the public API?   | RAML/OAS                                    | APIKit routes and HTTP listeners         |
| How is data mapped?       | External/inline DataWeave                   | Schema types and MUnit assertions        |
| How are failures handled? | Flow and global error handlers              | Error response transforms and tests      |
| What connects externally? | Connector configs and operations            | Property keys and architecture docs      |
| What must be configured?  | Property references and committed templates | Deployment workflow inputs               |
| What is tested?           | MUnit suites and assertions                 | CI commands and coverage config          |
| How is it deployed?       | Maven plugin and CI/deploy configuration    | Existing runbook                         |

When primary evidence and an API specification disagree, document the mismatch instead of choosing
silently. A declared contract and runtime implementation can both be important facts.

## Flow analysis

For every top-level flow, capture:

- flow name and source file
- trigger type and relevant path/topic/schedule without secret connection values
- direct processor sequence
- referenced subflows/private flows
- choice, scatter-gather, async, until-successful, retry, batch, and transaction scopes
- connector operations and configuration references
- variables that carry routing, correlation, entity, or state decisions
- local error handling and propagation/continuation behavior

Follow `flow-ref` edges until the business path is understandable. Detect cycles and stop revisiting
the same flow; a recursive or cyclic reference is a fact to document, not a reason to recurse
forever.

Separate these paths when they differ materially:

- primary success path
- alternate business branch
- asynchronous handoff
- retry/fallback path
- terminal error path

Do not list every logger or set-variable as a standalone architectural step. Group low-level
processors into meaningful stages while retaining exact flow references.

Infer an API-led layer only from explicit evidence such as project documentation, deployment
metadata, or stable naming and dependencies considered together. If the evidence is only a suffix,
say `inferred from project convention`.

## Contracts and transformations

For RAML/OAS and APIKit projects:

- enumerate resources, methods, URI/query parameters, headers, security schemes, and status codes
- locate request/response types and examples rather than copying the entire specification
- cross-check route existence and method/path bindings in Mule XML
- distinguish required fields from examples and defaults
- identify correlation headers and response/error envelopes

For event, queue, and scheduler-driven projects, document the trigger contract instead of forcing an
HTTP endpoint model. Include topic/queue/event type, payload schema source, acknowledgement or
retry semantics, and downstream side effects when evidenced.

For DataWeave:

- explain input and output media types
- summarize field mapping, filtering, grouping, defaults, and type coercion
- identify external lookup dictionaries and environment-specific mappings
- record which flow invokes the transform
- cite the `.dwl` path or inline transform location

Never assert a required mapping because a field merely appears in an example. Prefer schema
constraints, explicit validation, or tested failure behavior.

## Configuration and deployment

Document property keys, their source files, and their role. Do not copy values. Classify a property
as required, optional, or defaulted only when the source proves that status.

Describe connector configurations with:

- connector type and configuration name
- authentication mechanism when directly visible
- property references used for host/account/identity settings
- operations invoked by flows
- timeout, pooling, reconnection, TLS, or retry settings when explicitly configured

Treat secure property files, keystores, certificates, `.env` files, and deployment secrets as
boundaries. State how they are supplied; do not open or reproduce their contents.

Derive deployment steps from the Mule Maven plugin, CI workflow, runtime descriptors, and committed
environment templates. Do not invent CloudHub generation, Runtime Fabric topology, worker sizing,
or API Manager policies from generic Mule knowledge.

## Testing and operational behavior

Summarize MUnit by behavior, not only suite count:

- happy paths and alternate branches
- connector mocks and expected calls
- error-handler coverage
- transformation assertions
- scheduler, batch, or asynchronous test limitations

For operations, look for:

- schedulers and batch completion paths
- queues, dead-letter behavior, acknowledgements, and max concurrency
- retry policies, `until-successful`, and reconnection strategies
- correlation identifiers and structured logging
- alerts, notification flows, and health endpoints
- object-store state, watermarking, idempotency, and deduplication

Document only observable operational behavior. Put suggested monitoring or missing tests in a
clearly labeled recommendation section, never in the current-state description.

## Common interpretation traps

- A flow name is not proof of its business purpose.
- An API spec is not proof that every route is implemented.
- A listener path is not proof of the externally exposed base URL.
- A property key is not proof that a value is required or correctly configured.
- `on-error-continue` and `on-error-propagate` have materially different caller behavior.
- A retry wrapper does not guarantee idempotency.
- A connector config does not prove every operation uses it.
- A checked-in example payload may be synthetic, stale, or sensitive.
- A successful Maven package does not prove MUnit ran.
- A README architecture diagram is evidence of intent, not runtime truth.
