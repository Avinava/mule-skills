# mule-lint standards protocol

Use mule-lint as the authority for cross-project Mule engineering standards. This reference defines
how a skill loads that authority; it does not restate the practices.

1. If the mule-lint MCP server is available, read `mule-lint://standards` and select standards whose
   applicability and category match the work. Read `mule-lint://standards/{id}` for classification,
   source references, and the relevant guide slug.
2. Read `mule-lint://rules` or `mule-lint://rules/{id}` when an executable check, severity, status,
   or profile membership matters. Do not infer a standard solely from a rule name.
3. Read the focused `mule-lint://docs/{slug}` guide for implementation detail. Treat vendor
   requirements, recommended practices, and opinionated conventions as distinct claims.
4. If MCP is unavailable, use <https://avinava.github.io/mule-lint/> and disclose that structured
   catalog or lint execution was unavailable. Do not replace it with remembered or copied guidance.
5. Run lint after changing source when the repository and task permit it. Reading a standard is not
   evidence that the project conforms, and a clean lint result covers only implemented rules.

Use `recommended` for ordinary development and review, `baseline` when only high-confidence vendor
requirements are in scope, and `strict` for an explicitly requested comprehensive convention gate.
Experimental rules require explicit opt-in and must not be presented as stable standards.

## Execution evidence and compatibility

Prefer the canonical report when the installed server supports it. MCP returns the envelope directly
in `structuredContent`: `schemaVersion` (currently numeric `1`), `execution`, and `findings` are
**top-level fields**, not nested under `report` or mixed into legacy text. The CLI equivalent is
`--format report-json`. Existing `--format json` remains a flat finding array; never assume it is
an execution envelope. Keep legacy MCP text available for display, not as a second source of counts.

Before interpreting finding counts, inspect `execution.status`:

- `complete`: the selected analysis finished. Findings and gate results describe only its recorded
  scan scope, profile, enabled rules, selection, exclusions, and baseline context.
- `incomplete`: parsing, rule execution, or another analysis stage failed. Report diagnostics and
  coverage gaps even if there are zero visible findings. Never label this a passed or clean scan.
- `no-files`: no analyzable files were selected. Report the scope problem; this is not a clean scan.

Check diagnostics and process/tool errors as well as the envelope. Quiet output, baseline suppression,
severity filtering, permissive gates, and an empty finding array cannot establish completeness.
If `scan.scopeKnown` is false or scope information is absent, disclose unknown coverage instead of
claiming the whole project was checked. A complete scan is not a complete security assessment.
Preserve stable finding identity, rule ID, location kind (project or file), severity, remediation,
and standard references when reporting; do not invent confidence or evidence, or turn a project
location into line zero.

With an older pinned release that lacks the envelope, retain its supported legacy behavior and
explicitly label execution completeness unverified. Do not infer it from zero issues, quality
ratings, or process success alone. A task that requires verified completeness remains unresolved
until a compatible executable is available and checked. Do not silently change package pins to an
unpublished version.

## Responsibility boundary

mule-lint owns engineering standards and static analysis. mule-build owns local execution, test
orchestration, packaging, and its documented secure-reference preconditions. anypoint-connect owns
authorized platform operations. Skills compose these independent packages; build and connector do
not require a mandatory lint dependency. A secure-reference precondition is a narrow packaging
check, not proof of encryption correctness, runtime secret handling, vulnerability absence, or a
full security audit. Report exactly which checks ran and the gaps left behind.
