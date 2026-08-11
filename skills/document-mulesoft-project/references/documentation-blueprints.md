# Documentation blueprints

## Contents

1. [Adaptive output rules](#adaptive-output-rules)
2. [Business context](#business-context)
3. [README](#readme)
4. [Architecture](#architecture)
5. [API contract](#api-contract)
6. [Onboarding](#onboarding)
7. [Operations](#operations)
8. [Flow catalog](#flow-catalog)
9. [Targeted updates](#targeted-updates)
10. [Writing standards](#writing-standards)

## Adaptive output rules

Prefer a linked documentation suite that lets each audience stop at the right depth.

| Evidence                               | Document action                                  |
| -------------------------------------- | ------------------------------------------------ |
| Valid Mule project                     | Maintain a concise README and architecture guide |
| Public API or listener contract        | Add or maintain an API contract guide            |
| Reproducible setup/deployment evidence | Add or maintain onboarding                       |
| Nontrivial runtime operations          | Add or maintain operations guidance              |
| More than ten top-level flows          | Move detailed flow inventory to a flow catalog   |

Do not create placeholder-only files. If evidence is incomplete, keep a short `Open questions`
section in the closest applicable document.

Before editing, map existing documents to these roles. Reuse an existing `DESIGN.md`, runbook, or
API guide when it already owns the topic. Preserve document topology and manual narrative.

## Business context

Inspect source and existing prose before asking for context. When business purpose, audience,
ownership, terminology, criticality, compliance, or operational expectations remain material and
unknown, offer the user a short optional checkpoint before drafting.

Derive multiple-choice options from the repository when possible. Keep them neutral, add an
open-ended option, and always make `Not sure / Skip` explicit. Do not ask more than five questions
at once or block progress on unanswered business questions.

Treat answers as stakeholder-provided context. Attribute them when included, and cross-check any
claim about implemented behavior against source. When the user skips a material item, either omit
the unsupported claim or retain a concise, actionable question in the closest owning document.

## README

Keep the README useful in the first two minutes. Include:

1. Project purpose and directly evidenced API-led role; attribute stakeholder-provided purpose
   when source does not establish it.
2. A compact capability or trigger summary.
3. A small system-context or request-flow diagram when useful.
4. Runtime/build prerequisites.
5. Minimal local validation commands proven by the POM or workflows.
6. Links to deeper documentation.

Avoid exhaustive endpoint tables, full configuration catalogs, and detailed flow-by-flow prose in
the README. Link to the owning document instead.

## Architecture

Structure `docs/architecture.md` around questions:

1. **Overview:** What boundary does this application own?
2. **System context:** What calls it and what does it call?
3. **Primary runtime path:** How does one representative request/event move end to end?
4. **Flow organization:** Which listeners, orchestrators, reusable flows, and connectors matter?
5. **Data transformation:** Where are schemas, DataWeave, and lookups applied?
6. **Error handling:** What continues, propagates, retries, writes back, or notifies?
7. **Configuration and trust boundaries:** Which references configure authentication and external
   systems without exposing values?
8. **Design decisions:** Which choices are explicitly documented or strongly evidenced, and why?
9. **Extension points:** How is a new entity, route, mapping, or event added?
10. **Known gaps:** What could not be verified?

Use repository-relative source paths near detailed claims. A component table should explain
responsibility and collaborators, not merely repeat filenames.

## API contract

Create `docs/api-contract.md` only for an evidenced public or internal contract. Include:

- base path as declared, without inventing deployed hostnames
- endpoint/event/topic summary
- parameters and headers
- authentication/security scheme at the contract level
- request and response types
- success and error status/envelopes
- correlation behavior
- protocol or entity support matrix when it clarifies real variation
- documented mismatches between specification and implementation

Use sample payloads only when they are synthetic or safely sanitized. Prefer schema fragments over
copied production-like examples. State whether a rule comes from schema validation, flow logic, or a
test.

## Onboarding

Create `docs/onboarding.md` when a new engineer can follow evidence-backed steps. Include:

1. Tool, runtime, Java, and access prerequisites.
2. Safe configuration workflow using property names and placeholders.
3. Local build, lint, test, and run commands from the repository.
4. External-system setup steps only when the project contains enough evidence.
5. Deployment steps and runtime inputs from committed automation.
6. A validation checklist tracing one representative transaction.
7. Troubleshooting symptoms tied to actual code or configuration.

Never put a real username, hostname, tenant identifier, certificate path from a private machine, or
secret value in onboarding examples.

## Operations

Create `docs/operations.md` when runtime behavior extends beyond a simple request/response service.
Include applicable sections:

- trigger schedules and batch stages
- queue/topic processing and concurrency
- retry, timeout, reconnection, and dead-letter behavior
- state, watermark, deduplication, and idempotency boundaries
- correlation and log categories
- alerts and notification routes
- health checks and expected success signals
- safe incident triage using source-backed identifiers
- known failure modes and recovery steps

Separate current behavior from recommendations. Do not promise recovery, exactly-once delivery, or
ordering unless the implementation proves it.

## Flow catalog

Create `docs/flows.md` when the project has more than ten top-level flows or several distinct
domains. Group flows by trigger or capability. For each flow, include:

| Field            | Content                                                      |
| ---------------- | ------------------------------------------------------------ |
| Flow             | Exact name and source path                                   |
| Trigger          | Listener, scheduler, queue, event, batch, or invocation-only |
| Purpose          | Directly evidenced behavior or clearly marked inference      |
| Main stages      | Meaningful processor groups                                  |
| Collaborators    | Referenced flows, connectors, transforms                     |
| Failure behavior | Local/global handler outcome                                 |
| Tests            | MUnit coverage when found                                    |

Do not reproduce every processor attribute. Link back to architecture for shared behavior.

## Targeted updates

For requests such as `update the order flow documentation`:

1. Read the current owning document and linked context.
2. Re-inventory the project.
3. Trace the requested flow and its dependencies.
4. Update only the owned section and affected diagrams, indexes, and cross-references.
5. Preserve all unrelated manual content.
6. Report any nearby stale facts without expanding scope unless correctness requires it.

For a documentation audit, do not rewrite by default. Produce a prioritized gap list with evidence,
affected files, and recommended owning document.

## Writing standards

- Lead with behavior and outcome, then implementation detail.
- Use present tense for current behavior.
- Use repository-relative paths and exact flow/property names in code formatting.
- Distinguish `Verified`, `Provided`, `Inferred`, and `Unresolved` when confidence matters.
- Attribute stakeholder-provided business context and do not present it as verified runtime
  behavior.
- Keep one fact in one owning document and link rather than duplicate.
- Prefer neutral prose over sales language.
- Avoid decorative icons and excessive callouts.
- Keep code excerpts short and redact all sensitive values.
- Explain why a design matters to callers, maintainers, or operators.
- End each deep document with compact source references or open questions when useful.
