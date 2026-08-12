---
name: review-mulesoft-project
description: Review MuleSoft Mule 4 working changes, commit ranges, branches, pull requests, whole repositories, or release readiness and return prioritized evidence-backed findings with remediation options. Use for code review, PR review, project health audits, architecture and contract consistency checks, incident-prevention reviews, and pre-release gates covering Mule XML, RAML/OAS, DataWeave, connectors, configuration, MUnit, deployment, operations, security, privacy, and documentation. Review and report by default; do not modify source, post comments, approve changes, or perform release actions unless the user explicitly requests them.
---

# Review MuleSoft Project

Review the requested Mule 4 scope from behavior, contract, delivery, operational, security, test,
and maintainability perspectives. Find material defects and useful improvements without turning the
review into a style inventory or an implementation task.

## Privacy and reuse boundary

- Treat source, logs, payloads, application names, endpoints, organization metadata, correlation
  identifiers, and deployment details as potentially sensitive.
- Never copy identity, topology, fields, endpoints, schedules, volumes, incidents, log text, or
  tuning values from a prior project into this skill, a fixture, or another project's review.
- Use current-project identity only when necessary to make an authorized finding actionable. Never
  expose secrets, tenant identifiers, private hosts, personal data, raw payloads, or deployer names.
- Use neutral roles and synthetic values in reusable examples.

## Load the review guidance

Read these files directly from this skill folder for every review:

1. [Review domains](references/review-domains.md) for evidence routing and domain checks.
2. [Finding policy](references/finding-policy.md) for severity, confidence, deduplication, report
   structure, and readiness verdicts.

Route to sibling Mule skills only when their specialized workflow is material to the review. Do not
load every sibling skill by default, and do not fail when one is absent:

- Read `../mule-development/SKILL.md` and its post-development checklist when a changed Mule
  implementation or contract needs checks beyond the bundled review domains.
- Read `../mule-troubleshooting/SKILL.md` when a suspected defect requires causal analysis.
- Read `../mule-ops/SKILL.md` only for authorized runtime verification.
- Read `../document-mulesoft-project/SKILL.md` when using its inventory, documentation audit,
  privacy checks, or Mermaid guidance.

This review skill owns review scope, evidence policy, and interactive report formatting. Treat
sibling instructions as specialized helpers; their stop conditions and durable-document path rules
do not override this skill. If a dependency is unavailable, use the bundled review guidance and
disclose the coverage gap.

## Select the review mode

Use the mode explicitly requested by the user. If the request says only `review this project` or is
otherwise ambiguous, ask the user to choose:

1. **Change review:** working tree, staged changes, untracked text files, commit range, branch, or PR.
2. **Project review:** the complete current Mule repository.
3. **Release readiness:** the selected revision's readiness to release without performing a release.

Do not silently replace one mode with another. Resolve the exact review boundary, repository
instructions, and only the revision metadata relevant to the selected mode before asking for
discoverable facts.

## Workflow

### 1. Establish the exact review target

- Resolve the Mule project root to a real path and preserve unrelated user changes.
- Confirm direct Mule evidence such as Mule XML, DataWeave, RAML/OAS, MUnit, `mule-artifact.json`,
  compatible Maven packaging, the Mule Maven plugin, or Mule-specific tooling and fixtures. A
  partial fixture or Mule-focused tooling repository is reviewable when that boundary is explicit;
  do not represent it as a deployable Mule application. Stop only when the requested scope has no
  relevant Mule implementation, contract, test, deployment, or tooling evidence.
- Record mode, target revision or files, base and head when applicable, and exclusions requested by
  the user.
- Read repository instructions before running commands or interpreting conventions.

For change review:

- For a PR, use its actual base and head metadata and review the merge diff.
- For a branch, use the merge base with the upstream default branch unless the user names another
  base.
- For a commit range, use the supplied endpoints.
- For working changes, include staged, unstaged, and untracked text files.
- For a revision not checked out in the working tree, inspect blobs from that revision and run
  validation from an immutable temporary snapshot such as `git archive` extracted under a verified
  `mktemp` directory. Never interpret current-working-tree inventory or test results as evidence for
  the historical revision.
- Inspect affected callers, referenced flows, contracts, tests, configuration, documentation, and
  operational behavior outside the diff when necessary to validate impact.

For project review, inventory the entire requested boundary before choosing deep paths. When the
target is a nested fixture or module, inspect only the directly relevant parent harness,
instructions, and consumers outside that boundary. For readiness, review the current or named
release candidate and the repository's actual release policy.

### 2. Build the evidence map

Use the documentation skill's read-only inventory when available:

```bash
python3 ../document-mulesoft-project/scripts/inventory_mule_project.py <project-root> --pretty
```

The inventory's project classification is one signal, not a veto: reconcile it with direct source
and the requested boundary. Then inspect relevant source directly. Build a working ledger of material claims and their
repository-relative paths, symbols, flows, endpoints, property keys, tests, or runtime signals.
Record contradictions instead of silently choosing one source.

### 3. Offer optional business context

After technical inspection, surface only missing business information that would materially change
impact, severity, readiness, or remediation. Examples include criticality, ownership, compliance,
recovery expectations, ordering, or acceptable data loss. Do not delay the technical review: put
the optional questions in Open questions and invite the user to answer any item for a refined review.

- Ask no more than five questions in one batch.
- Provide two to four evidence-informed options plus `Other (please specify)` and
  `Not sure / Skip` where practical.
- State that each item and the entire checkpoint are optional.
- If the user answers, revise the affected findings or verdict. If the user skips, retain the
  applicable evidence gap and use `Unresolved` for readiness only when it prevents a defensible gate.
- Treat answers as provided context, not proof of implemented behavior.

### 4. Review by domain

Apply every relevant domain from `references/review-domains.md`. Those domains encode the same
mechanism classes as `mule-development` (value contracts, expression embedding, contract authority,
failure disposition, state/idempotency). For change review, focus on changed behavior and directly
affected dependencies. For project and readiness reviews, cover all domains and disclose any area
not inspected.

Prioritize behavioral correctness, contract compatibility, security, delivery semantics, failure
outcomes, operability, and test evidence. Put non-defect design and maintainability suggestions in a
separate Improvements section capped at five items.

### 5. Run proportionate validation

Run safe, relevant checks when available:

- parsers and contract validation
- Mule lint and security checks
- focused MUnit tests for affected behavior
- documentation privacy/link audit
- repository-required build or package checks

Do not skip tests by default, but do not make every change review run an unrelated full build. For
release readiness, run the complete validation and test path required by repository policy. A failed
required check makes the candidate not ready; a check that cannot run can make readiness unresolved.

Do not mask a failure by rerunning with weaker options. Report commands, scope, results, skipped
checks, tool failures, and generated-only artifacts.

For deliberately incomplete or negative fixtures, judge nonzero validation results against the
fixture's evidenced expected outcomes. An expected diagnostic is coverage evidence, not a product
defect; an undocumented or unasserted failure remains a gap.

### 6. Decide findings and readiness

Apply `references/finding-policy.md` exactly:

- Report only evidence-backed defects or risks as findings.
- Assign severity and confidence independently.
- Group repeated symptoms under one root cause.
- Include actionable remediation options and a validation method.
- Keep low-confidence suspicions in Open questions.
- Issue a four-state verdict only in release-readiness mode.

### 7. Deliver the review

Return Markdown directly unless the user requests a durable report. Lead with findings ordered by
severity, then improvements, open questions, and coverage. If there are no findings, say so and list
the checks performed and residual gaps; never claim the project is defect-free.

For historical revisions, link to a revision-pinned repository URL when one is available. Otherwise
cite `relative/path@revision:line` as text; do not link to a different working-tree version.

For GitHub PRs, report findings with exact paths and lines but do not post inline comments, submit a
formal review, approve, request changes, or change PR state unless explicitly requested.

## Non-negotiable rules

- Do not modify source, configuration, tests, documentation, or PR state during a review-only task.
- Do not infer behavior from names alone or present generic Mule guidance as a project finding.
- Do not call a temporal correlation a root cause without discriminating evidence.
- Do not report cosmetic preferences as defects; use the capped Improvements section when useful.
- Do not recommend numeric concurrency, timeout, retry, or pool values without current-project
  workload and dependency evidence.
- Do not expose secret values or sensitive log and payload content in findings.
- Do not give `Ready` when required evidence is missing or a required check was skipped or failed.
