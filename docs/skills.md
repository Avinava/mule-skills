# Skills

Eight skills, shared and host-neutral. Claude Code loads them from the plugin; every other host reads
them from `.agents/skills/`. Each has a `SKILL.md` the agent selects from its description, so
describing the task is usually enough.

| Skill | Primary job | Default effect | What you receive |
| --- | --- | --- | --- |
| [`mule-api-design`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-api-design) | Shape or assess an HTTP API contract | Read-only workshop or assessment; writes local RAML/OAS only when authoring is requested; Design Center mutations are separate | Decision ledger, operation model, contract or findings, and validation evidence |
| [`mule-docs`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-docs) | Explain the current Mule project for a named audience | Writes only the requested documentation scope | Evidence-backed Markdown/Mermaid, source map, and clearly labeled gaps |
| [`mule-development`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-development) | Implement Mule XML, DataWeave, APIKit, connector, or configuration behavior | Changes production source/configuration inside the requested scope | Implemented behavior, changed-file summary, validation evidence, and remaining gaps |
| [`mule-testing`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-testing) | Author or repair behavior-focused MUnit coverage | Changes tests, fixtures, mocks, and test-only configuration | Test intent, focused/full results, and any unproven behavior |
| [`mule-troubleshooting`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-troubleshooting) | Diagnose incidents and failures | Read-only diagnosis by default | Root-cause assessment or ranked hypotheses, confidence, evidence gaps, and fix plan |
| [`mule-ops`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-ops) | Assess runtime health and deployment evidence | Read-only telemetry analysis by default | Health assessment, evidence coverage, risks, and recommended actions |
| [`mule-review`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-review) | Review changes, repositories, PRs, or release readiness | Read-only; no implementation, comment, or PR-state change unless requested | Prioritized findings, fix options, coverage limits, and a readiness verdict when applicable |
| [`mule-build`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-build) | Run local readiness, security, MUnit, packaging, and release-preparation gates | Creates `target/` artifacts during packaging; source/Git changes require an explicit version or release request | Exact checks, test totals, artifact or failure evidence, and release actions performed |

See [Mule Skills in action](see-it-in-action.md) for an evidence-backed change journey and a
read-only risk review. The examples deliberately show a blocked test gate rather than presenting a
tests-skipped package as a successful release.

## Choosing the right skill

| Request | Start with | Add when needed |
| --- | --- | --- |
| Design or assess an HTTP API contract | `mule-api-design` | Development for Mule/APIKit implementation after approval |
| Explain or refresh the project | `mule-docs` | Optional business-context questions when source cannot establish purpose or ownership |
| Implement a change | `mule-development` | Documentation refresh, then change review |
| Add or repair MUnit tests | `mule-testing` | `mule-build` for execution; development if a product defect is exposed |
| Diagnose a symptom | `mule-troubleshooting` | `mule-ops` for authorized runtime evidence; development only when a fix is requested |
| Assess current runtime health | `mule-ops` | `mule-troubleshooting` when a specific causal question emerges |
| Review a change or repository | `mule-review` | `mule-ops` only for authorized, material runtime verification |
| Prepare a release | `mule-build` | Release-readiness review before commit/tag; `mule-ops` for separately approved publish/deploy |

## What they read

Every skill reads `AGENTS.md` for shared project context, which is why
[project setup](project-setup.md) matters more than the install itself. Skills refer to their bundled
references and scripts through `<skill-root>` and `<skills-root>` placeholders, so the same file works
under a plugin install and a vendored install.

Documentation and review questions are optional and non-blocking. When business information would
materially improve the result, the skill offers concise choices plus `Other` and `Not sure / Skip`,
then continues with verified technical evidence if you skip.

## Runtime evidence is gated, not assumed

`mule-api-design`, `mule-ops`, `mule-troubleshooting`, and `mule-review` confirm Anypoint access
before their first connector call, and offer setup, supplied exports, or a
repository-only scope when it is missing. See [Anypoint access](anypoint-access.md).

## Example prompts

```text
Use mule-docs to refresh architecture and operations documentation. Ask optional business questions
with choices where the repository cannot establish important context.

Use mule-api-design to turn these requirements into a consumer-centered RAML or OAS contract.

Use mule-development to implement this Mule change and complete the post-development checklist.

Use mule-testing to add faithful MUnit coverage for this behavior, then run the focused and required
full tests without weakening assertions or mocks.

Use mule-troubleshooting to find the root cause of the timeouts in this flow, then stop before
changing anything.

Use mule-ops to check this application's health for the last six hours. If Anypoint access is not
configured, tell me what you need instead of guessing.

Use mule-review in change-review mode for this branch. Report findings and fix options; do not
modify source or PR state.

Use mule-build to validate and package this application without performing any release action.
```

Under a Claude Code plugin install, skills are namespaced, so `mule-skills:mule-review` invokes one
directly.
