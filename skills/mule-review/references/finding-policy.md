# Finding and readiness policy

## Contents

1. [Evidence and confidence](#evidence-and-confidence)
2. [Severity](#severity)
3. [Finding qualification](#finding-qualification)
4. [Remediation options](#remediation-options)
5. [Release-readiness verdicts](#release-readiness-verdicts)
6. [Report format](#report-format)
7. [No-finding behavior](#no-finding-behavior)

## Evidence and confidence

Keep evidence state separate from finding severity:

| Evidence state | Meaning |
| --- | --- |
| Verified | Directly established by source, contract, test, configuration, or telemetry |
| Provided | Business context supplied by the user or stakeholder |
| Inferred | Strongly suggested by multiple facts but not explicitly established |
| Unresolved | Missing or contradictory evidence prevents a conclusion |
| Recommended | Proposed improvement, not current behavior |

Assign confidence to each finding:

- **High confidence:** direct evidence demonstrates the failure or broken invariant.
- **Medium confidence:** the mechanism and multiple evidence points strongly support the risk, but a
  specific runtime or consumer fact remains unverified.
- **Low confidence:** plausible but missing a discriminating check. Do not report it as a finding;
  move it to Open questions with the next check.

Never increase severity to compensate for low confidence.

## Severity

Use the highest credible impact of the evidenced mechanism, not the loudness of logs or size of diff:

| Severity | Definition |
| --- | --- |
| Critical | Credible security exposure, secret disclosure, unrecoverable corruption, data/message loss, or behavior that makes release predictably catastrophic |
| High | Likely incorrect results, outage, public contract break, or serious operational failure on a normal or critical path |
| Medium | Meaningful edge-case, reliability, observability, test, deployment, or maintainability risk that is not independently release-blocking |
| Low | Localized defect with limited impact and a clear safe workaround |

Put non-defect design, readability, consistency, or maintainability ideas under **Improvements**, not
Low findings. Cap Improvements at five and include only evidence-backed, actionable suggestions.

## Finding qualification

Report a finding only when all are present:

1. A specific affected behavior or invariant.
2. Repository-relative file and line evidence, an explicitly identified runtime source, or a
   precise absence established by an inventory, manifest, command, or expected repository location.
3. A concrete failure mechanism or compatibility problem.
4. Credible user, data, operational, security, or maintenance impact.
5. A practical validation method.

Do not report:

- generic best practices with no project-specific violation
- cosmetic style preferences
- behavior inferred only from a flow, application, or property name
- duplicate symptoms of an already reported root cause
- stale issues outside a change-review scope unless they make the change unsafe
- speculative runtime problems without coverage or a discriminating check

For a pre-existing issue that blocks safe review of a change, label it `Pre-existing dependency` and
explain why the new change depends on it.

## Remediation options

Give one preferred option when evidence supports it. Give two or more options when the correct choice
depends on an unresolved business, compatibility, performance, or delivery tradeoff.

For every option state:

- intended behavior
- main tradeoff or compatibility impact
- exact validation signal

Do not provide a large implementation plan by default. Do not modify files unless the user follows
up with an implementation request.

## Release-readiness verdicts

Issue a verdict only in release-readiness mode:

| Verdict | Rule |
| --- | --- |
| Ready | Required validation passes, no Critical or High findings exist, and no material evidence gap remains |
| Ready with conditions | No active Critical or High finding exists; only explicit non-blocking actions or accepted Medium/Low risks remain |
| Not ready | A Critical or High release blocker exists, or a required lint, security, test, package, contract, or deployment check fails |
| Unresolved | Missing access, unavailable tooling, skipped required checks, ambiguous candidate, or incomplete evidence prevents a defensible gate |

Do not convert a failed required check to Unresolved. A check that runs and fails is `Not ready`; a
check that cannot run is normally `Unresolved` unless other evidence already makes the candidate not ready.

## Report format

Lead with findings. Omit empty sections except Coverage and residual risk.

```markdown
# MuleSoft review

**Mode:** Change | Project | Release readiness
**Target:** <working tree, range, PR, repository, or release candidate>
**Verdict:** <readiness modes only>

## Findings

### [High] Concise outcome-based title
**Confidence:** High
**Impact:** What fails and who or what is affected.
**Evidence:** `relative/path.xml:123` and the relevant symbol or contract, or the exact absence check.
**Mechanism:** Why the current behavior produces the impact.
**Options:** Preferred remediation and material alternatives with tradeoffs.
**Validation:** Exact check that proves the issue is resolved.

## Improvements
Up to five non-defect improvements.

## Open questions
Only unresolved items that could change impact, severity, or readiness.

## Coverage and residual risk
Files and domains reviewed, commands run, results, skipped checks, tool failures, runtime coverage,
and areas not inspected.
```

Sort findings by Critical, High, Medium, then Low. Within a severity, put wider impact and higher
confidence first. Use exact clickable file links in interactive responses when supported. Pin
remote links to the reviewed revision; if that is not possible, use
`relative/path@revision:line` text rather than a misleading working-tree link. Use
repository-relative paths in durable repository documents.

For PR reviews, produce this report without posting comments. If the user explicitly requests draft
comments, additionally provide one concise comment per finding at the narrowest defensible line.

## No-finding behavior

When no findings qualify, say `No material findings in the reviewed scope.` Then state:

- exact scope and revision
- validations performed and results
- domains or paths not inspected
- required checks that could not run
- residual risks from missing runtime, business, consumer, or environment evidence

Do not say `approved`, `safe`, `bug-free`, or `production-ready` outside release-readiness mode and its
defined verdict rules.
