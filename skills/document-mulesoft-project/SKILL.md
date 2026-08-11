---
name: document-mulesoft-project
description: Analyze MuleSoft Mule 4 repositories and create or update evidence-backed Markdown documentation with Mermaid diagrams. Use for project overviews, architecture and flow documentation, API contracts, connector and DataWeave documentation, configuration guides, onboarding, deployment, operations, testing, troubleshooting, or documentation-gap audits. Use for full-project documentation and targeted refreshes after Mule XML, RAML/OAS, DataWeave, MUnit, configuration, or deployment changes. Do not use for generic non-Mule repositories or source-code changes unrelated to documentation.
---

# Document MuleSoft Project

Create documentation that explains what the project does, how requests and data move through it,
how it fails, and how another engineer can operate or extend it. Derive claims from repository
evidence and prefer a small, navigable document set over a single exhaustive dump.

## Inputs and outputs

Accept a Mule project root and an optional requested scope such as architecture, one flow, API
contract, onboarding, or a full refresh. Default to the current repository and an adaptive
documentation suite when the user does not narrow the request.

Write only documentation files unless the user explicitly requests source changes. Preserve
existing filenames and structure when they already serve the same purpose.

## Load the references

Read these files directly from this skill folder:

1. Always read [MuleSoft analysis](references/mulesoft-analysis.md) before inspecting a project.
2. Read [documentation blueprints](references/documentation-blueprints.md) before choosing output
   files or editing existing documentation.
3. Read [Mermaid guide](references/mermaid-guide.md) whenever the output includes diagrams.
4. Always read [privacy and evidence](references/privacy-and-evidence.md) before writing or
   validating output.

Do not load unrelated references from other skills unless the task independently requires them.

## Workflow

### 1. Establish scope and safety

- Read repository instructions and existing documentation before generating content.
- Resolve the project root to a real path. Do not follow symlinks outside it.
- Ignore `.git`, dependency caches, build output, generated sources, IDE metadata, certificates,
  keystores, and binary files.
- Treat configuration values, environment files, logs, fixtures, and examples as potentially
  sensitive. Never decrypt secrets.
- If the requested root is not a Mule project, report the evidence checked and stop without
  creating generic documentation.

### 2. Build a deterministic inventory

Run the bundled inventory tool and inspect its JSON before reading individual implementation files:

```bash
python3 <skill-root>/scripts/inventory_mule_project.py <project-root> --pretty
```

Use the inventory to route deeper inspection. Verify important behavior in the actual source files;
the inventory is an index, not a substitute for reading code.

Inspect, when present:

- `pom.xml` and `mule-artifact.json`
- `src/main/mule/**/*.xml` and global error handlers
- RAML/OAS specifications and examples
- external and inline DataWeave
- property references and environment templates
- MUnit suites
- deployment workflows and runtime configuration
- existing README and `docs/` content

### 3. Create an evidence ledger

Keep a working list of every material claim with its repository-relative source path and symbol,
flow, endpoint, or property key. Apply this precedence:

1. Runtime behavior: Mule XML and DataWeave.
2. Public contract: RAML/OAS, cross-checked against runtime listeners and APIKit routes.
3. Build and runtime versions: POM and Mule artifact metadata.
4. Configuration: referenced property keys and committed templates, never deployed values.
5. Tests: MUnit source and CI configuration.
6. Existing prose: contextual evidence only after verification.

Record contradictions as documentation gaps. Label a conclusion as inferred when the source does
not establish it directly. Put unresolved questions in a compact `Open questions` section instead
of inventing an answer.

### 4. Choose the adaptive document set

Create or reconcile:

| Condition                                                             | Output                                 |
| --------------------------------------------------------------------- | -------------------------------------- |
| Any valid Mule project                                                | `README.md` and `docs/architecture.md` |
| RAML/OAS, APIKit routes, or HTTP listeners                            | `docs/api-contract.md`                 |
| Evidenced local setup, configuration, or deployment steps             | `docs/onboarding.md`                   |
| Schedulers, queues, batch jobs, retries, notifications, or monitoring | `docs/operations.md`                   |
| More than ten top-level flows                                         | `docs/flows.md`                        |

Do not create an empty or speculative document merely to satisfy the table. If an existing document
already owns a topic, update it rather than creating a duplicate.

For a targeted request, update only the requested document and directly affected cross-references.

### 5. Explain from multiple perspectives

Cover the applicable perspectives without repeating the same facts:

- **Purpose and boundary:** the problem, actors, upstream/downstream systems, and API-led layer when
  directly evidenced.
- **Runtime path:** triggers, routing, transformations, connector calls, state changes, and response.
- **Contract:** endpoints/events, headers, payload shapes, correlation, and errors.
- **Failure behavior:** local/global handlers, retry or continuation semantics, writeback, and
  notification paths.
- **Configuration and security:** property names, secure-property boundaries, authentication
  mechanism, and trust boundaries without secret values.
- **Changeability:** extension points, design decisions, tests, deployment, operational checks, and
  known gaps.

Use tables for inventories and comparisons, prose for rationale, code snippets only when they make
an exact contract clearer, and Mermaid only when relationships or sequence benefit materially.

### 6. Reconcile existing documentation

- Preserve correct manually authored explanations and project-specific terminology.
- Change a claim only when source evidence contradicts it or the user requests a rewrite.
- Preserve unrelated sections, links, and document topology.
- Add source paths near detailed claims so a maintainer can verify them.
- Do not delete a document or collapse a multi-document suite without explicit approval.
- Use repository-relative links and paths; never publish local absolute paths.

### 7. Validate before delivery

Run the documentation audit over the files changed:

```bash
python3 <skill-root>/scripts/audit_documentation.py <documentation-root>
```

Then:

- Render or parse every new Mermaid block when a Mermaid renderer is available.
- Re-read the diff for unsupported claims and leaked values.
- Confirm links resolve and diagrams match the prose.
- Confirm no source code or configuration was modified unintentionally.
- Summarize files created or updated, evidence gaps, and validations performed.

## Non-negotiable rules

- Never copy credential values, tokens, passwords, private keys, certificates, keystores, real
  secret-property ciphertext, or sensitive log payloads into documentation.
- Never infer business guarantees from flow names alone.
- Never describe a connector, retry, transaction, security policy, or error mapping that is not
  evidenced.
- Never paste whole Mule XML or DataWeave files; explain behavior and cite the source location.
- Never replace customer/project identity in generated project documentation unless the user asks
  for anonymization, but always redact secrets and personal data.
- Never include examples or terminology from unrelated customer projects in this reusable skill.
