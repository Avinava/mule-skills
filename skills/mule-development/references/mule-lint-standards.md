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
