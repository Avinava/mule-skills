---
name: mule-development
description: Create or modify MuleSoft Mule 4 flows, DataWeave, error handling, connectors, queues, batch jobs, configuration, and MUnit tests using evidence-based project conventions and post-change validation. Use when implementing Mule application source or contract changes. Inspect runtime and connector versions before applying version-sensitive guidance, preserve existing contracts unless the user requests a breaking change, and route review-only work to the mule-review skill.
---

# MuleSoft Development

Develop against the current project's Mule runtime, connector versions, contracts, deployment
target, operational constraints, and repository instructions. Treat reusable examples as patterns to
adapt and verify, not project-independent guarantees.

## Load the required guidance

Read [the mule-lint standards protocol](references/mule-lint-standards.md), then load only the
standards, rules, and focused guides applicable to the change. mule-lint is the cross-project
standards authority; this skill owns the implementation workflow and project-specific reasoning.

Use [Invariant classes and cross-cutting gates](references/invariant-classes.md) as the canonical
mechanism reference. Read only the sections relevant to the changed path, plus every applicable
cross-cutting gate:

| Change | Read |
| --- | --- |
| DataWeave, variables, connector input/output, fixtures, batch values | Class A |
| XML attributes or CDATA containing `#[…]` | Class B |
| RAML/OAS, APIKit routes, event schemas, flow reachability | Class C |
| Error handlers, retries, fallback, batch/loop failures, acknowledgement | Class D |
| Object Store, caches, sources, watermarks, hashes, replay, creates/upserts | Class E |
| Any source change | Applicable cross-cutting gates |

After editing, read and complete
[Post-Development Checklist](resources/post-development-checklist.md). The checklist verifies the
reference; it is not a second tutorial.

## Mechanism model

Use five overlapping invariant classes:

| Class | Owns |
| --- | --- |
| **Class A — Value contracts** | Shape, type, media type, nullability, serialization, and fixture fidelity |
| **Class B — Expression embedding** | `#[…]` remains complete after XML and CDATA parsing |
| **Class C — Contract authority** | Which API or event contract governs behavior, and what is reachable |
| **Class D — Failure disposition** | Classification, retry, terminal outcome, acknowledgement, and attribution |
| **Class E — State and idempotency** | Caches, sources, watermarks, hashes, replay, and duplicate safety |

The classes are a reasoning aid, not an exhaustive compliance taxonomy. Apply these mandatory
cross-cutting gates wherever relevant:

- **Security and configuration:** authentication, authorization, TLS, secure properties, input
  trust, least privilege, and environment-safe configuration.
- **Capacity and lifecycle:** concurrency, back pressure, streaming and memory, timeouts,
  connections, deployment target, and graceful shutdown.
- **Delivery and transactions:** acknowledgement, redelivery, ordering, transaction participation,
  duplicate behavior, and recovery.
- **Privacy and observability:** safe logging, correlation, metrics, operational version identity,
  and no sensitive or prior-client material.
- **Validation and documentation:** representative tests, lint/package checks, contracts, runbooks,
  recovery steps, and project invariants.

Prioritize findings and validation by credible impact and evidence, not by class. A value or state
defect can be release-blocking when it risks incorrect results, duplicates, or data loss.

## Workflow

### 1. Establish the change boundary

1. Read repository instructions and the owning flow, callers, referenced flows, bound contract or
   event schema, DataWeave, configuration keys, effective error strategy, and relevant MUnit tests.
2. Confirm Mule runtime, Java, connector, plugin, and deployment-target versions before using
   version-sensitive syntax or semantics.
3. Record the behavior, caller/source outcome, delivery guarantees, state transitions, security
   boundary, and operational signals that must remain stable.
4. Identify which invariant classes and cross-cutting gates apply.
5. Decide the focused and integration validation before editing.

### 2. Implement the smallest coherent change

- Preserve public contracts unless the user explicitly requests and coordinates a breaking change.
- Match each value to its next consumer and validate required data before side effects.
- Keep embedded expressions syntactically complete after markup parsing.
- Change the authoritative bound contract or schema together with reachable implementation and
  consumers.
- Give each failure a classified, governed disposition; do not promise retry or recovery without an
  actual mechanism.
- Preserve idempotency and recovery across retries, redelivery, failed writeback, and deployment.
- Apply all relevant cross-cutting gates and preserve unrelated formatting and user-authored work.

### 3. Validate behavior and evidence

1. Run `python3 <skill-root>/scripts/check_embedded_expressions.py .` whenever
   Mule XML changes in an installed project. `<skill-root>` is this skill's own directory:
   `${CLAUDE_PLUGIN_ROOT}/skills/mule-development` when installed as a Claude Code plugin,
   `.agents/skills/mule-development` when vendored into the project.
2. Run the project's formatter or linter and focused MUnit tests for the changed path.
3. Exercise success, alternate, empty/invalid input, dependency failure, retry exhaustion or terminal
   disposition, and recovery paths that are material to the change.
4. Run the repository-required full build or package gate when policy or release scope requires it.
5. Complete `resources/post-development-checklist.md` and inspect the final diff.
6. Update bound contracts, schemas, operations guidance, recovery notes, `AGENTS.md` invariants, and
   documentation when behavior changes.

Report commands, results, skipped checks, tool failures, generated-only artifacts, and remaining
evidence gaps. Never weaken a required check to make it pass.

## Non-negotiable rules

- Never copy project, organization, application, endpoint, payload, identifier, schedule, volume,
  incident detail, topology, or tuning value from another client into reusable guidance or a new
  project.
- Never expose or add secrets, secure-property values, tenant details, private hosts, personal data,
  raw production payloads, or sensitive identifiers.
- Never infer runtime authority from an unbound contract copy or infer dead code from APIKit routing
  alone.
- Never retry all errors indiscriminately, swallow work that still requires processing, or create a
  terminal state merely to satisfy a generic rule.
- Never recommend numeric concurrency, timeout, retry, pool, TTL, or cache values without current
  workload, replica, runtime, and dependency evidence.
- Never assume packaging proves route alignment or embedded-expression evaluation.

## Version-sensitive references

Re-check current official documentation when installed versions differ:

- [Mule data types and DataWeave output inference](https://docs.mulesoft.com/mule-runtime/latest/mule-data-types)
- [DataWeave identifier rules](https://docs.mulesoft.com/dataweave/latest/dataweave-language-introduction#rules-for-declaring-valid-identifiers)
- [Until Successful scope](https://docs.mulesoft.com/mule-runtime/latest/until-successful-scope)
- [Batch processing and concurrency](https://docs.mulesoft.com/mule-runtime/latest/tuning-batch-processing)
- [Object Store connector reference](https://docs.mulesoft.com/object-store-connector/latest/object-store-connector-reference)
- [VM Connector behavior and deployment limitations](https://docs.mulesoft.com/vm-connector/latest/)
- [HTTP Connector reference](https://docs.mulesoft.com/http-connector/latest/http-documentation)
