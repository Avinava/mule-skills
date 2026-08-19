---
name: mule-api-design
description: Design, author, revise, or assess consumer-facing MuleSoft HTTP API contracts in RAML 1.0 or OpenAPI 3.0 using explicit resource, method, URI, data, error, security, compatibility, and governance decisions. Use for API design workshops, URL and naming guidance, new RAML/OAS contracts, contract-first changes, and contract-only reviews. Maintain RAML 0.8 or OAS 2.0 when required, but do not use for AsyncAPI, event schemas, Mule implementation, MUnit authoring, or general project review.
---

# Mule API Design

Design the interface from consumer tasks and domain concepts before writing syntax. Keep requirements,
decisions, assumptions, contract source, validation results, and platform mutations visibly distinct.

## Choose the mode

| User intent | Mode | Default result |
| --- | --- | --- |
| Requirements are incomplete or the user wants advice | Guided design workshop | Decision ledger, resource/operation matrix, unresolved choices, then a contract when requested |
| The user wants a new or revised contract | Author or revise | RAML/OAS source plus validation evidence and compatibility notes |
| The user wants design feedback only | Contract-only assessment | Prioritized consumer-impact findings; no source or Anypoint changes |

For Mule flow, APIKit, connector, or DataWeave implementation, hand off to `mule-development` after
the contract is coherent. Use `mule-testing` for MUnit, `mule-docs` for broader documentation,
`mule-review` for a whole change or release review, and `mule-build` for project build/release work.

## Load guidance progressively

Always read [Design workshop](references/design-workshop.md) and
[HTTP API design](references/http-api-design.md). Then load only what the task needs:

| Need | Read |
| --- | --- |
| Payloads, naming, errors, examples, privacy | [Data and errors](references/data-and-errors.md) |
| Pagination, concurrency, idempotency, async work, compatibility | [Contract patterns](references/contract-patterns.md) |
| RAML 1.0 authoring or RAML maintenance | [RAML 1.0](references/raml-1.0.md) |
| OpenAPI 3.0 authoring or OAS maintenance | [OpenAPI 3.0](references/oas-3.0.md) |
| Design Center, Exchange, or centralized governance | [Anypoint design workflow](references/anypoint-design.md) |

For any Anypoint work, also read
`<skills-root>/mule-ops/references/anypoint-readiness.md` before the first connector call.

## Workflow

### 1. Establish authority and constraints

Read repository instructions, existing bound contract, implementation bindings, published coordinates,
consumer evidence, and organizational standards. Determine the source of truth, target format/version,
consumers, trust boundary, compatibility promise, identifier/state ownership, governance profiles, and
whether the work is advisory, local-authoring, or includes Anypoint mutation.

Prefer RAML 1.0 or OpenAPI 3.0 for new work. Maintain RAML 0.8 or OAS 2.0 only when a verified tool,
consumer, or published contract requires it. APIKit does not support OAS 3.1; do not silently upgrade.

### 2. Ask bounded, high-impact questions

Ask only choices that materially change the public interface. Group related questions and recommend an
option with rationale. If the user cannot answer, record a labeled assumption and continue where the
decision is reversible. Never invent a business identifier, confidential domain fact, production URL,
tenant, payload, or organization convention.

### 3. Build the decision ledger and operation matrix

Record each consequential choice, alternatives, rationale, evidence, compatibility impact, and owner.
Map every consumer task to resource, URI, method, request, success response, error outcomes, security,
idempotency, pagination or concurrency behavior. Resolve contradictions before authoring syntax.

### 4. Design the HTTP and data contract

Apply HTTP semantics rather than CRUD folklore. Model stable resources and relationships, use methods
according to safety and idempotency, make errors actionable, and define representation semantics. Treat
URI naming, status codes, versioning, pagination, PATCH, async operations, and idempotency as contextual
decisions, not universal lint rules.

### 5. Author one source of truth

Match the selected specification and repository layout. Keep reusable components purposeful, references
resolvable, examples neutral and valid, security explicit, and operation identifiers stable. Do not keep
RAML and OAS as manually synchronized co-authoritative copies.

### 6. Validate locally

When `mule-lint` 1.28 or newer is available, run:

```bash
mule-lint api validate <api-project> --main <main-file> --format json
```

Add the repository-approved ruleset with repeatable `--ruleset` options. Use `--dependency-root` only for
an explicitly approved local dependency root. The validator must not fetch HTTP references. Distinguish
AMF functional conformance from governance conformance, fix execution/configuration failures rather than
reporting them as design findings, and never weaken a required profile to get a pass.

### 7. Preview every platform mutation

Local design needs no Anypoint access. For Design Center or Exchange work, follow
[Anypoint design workflow](references/anypoint-design.md). Use capability-specific readiness, exact project
identity, read-before-write, and preview-token tools. Project creation, file sync, and publication are three
separate approvals. Never use direct legacy publication in a new automated workflow. Never delete a project,
asset, branch, or file unless the user separately requests and approves that exact deletion.

### 8. Hand off downstream work

State what the contract requires from APIKit routing, implementation, MUnit, documentation, operations,
and release work. Invoke sibling skills only for the scope the user requested; a finished contract is not
proof that implementation, deployment, or centralized governance succeeded.

## Completion format

Report the outcome and source of truth, decision ledger and assumptions, operation matrix or findings,
compatibility/security implications, local validation evidence, redacted Anypoint actions, unresolved
decisions, and downstream handoffs.

## Non-negotiable boundaries

- Never place a client, organization, tenant, application, user, private host, real identifier, or raw
  production payload in reusable guidance, fixtures, examples, filenames, logs, commits, or reports.
- Never copy another project's API vocabulary, URLs, schemas, examples, tuning, or governance assumptions.
- Never claim a path or naming convention is a standard without source and scope.
- Never use GET or HEAD request bodies, promise idempotency without a mechanism, or make a breaking change
  without explicitly identifying affected consumers and migration behavior.
- Never publish, overwrite, or delete platform content merely because authentication works.
