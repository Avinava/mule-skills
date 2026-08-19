# Skills

Seven skills, shared and host-neutral. Claude Code loads them from the plugin; every other host reads
them from `.agents/skills/`. Each has a `SKILL.md` the agent selects from its description, so
describing the task is usually enough.

| Skill | Use it for | Default result |
| --- | --- | --- |
| [`mule-docs`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-docs) | Project documentation, architecture, APIs, flows, onboarding, operations, and targeted refreshes | Evidence-backed Markdown and Mermaid, plus clearly labeled gaps |
| [`mule-development`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-development) | Mule production XML, DataWeave, connectors, error handling, queues, batch, configuration, and contracts | Implemented source change with proportionate validation |
| [`mule-testing`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-testing) | Behavior-focused MUnit authoring, repair, fixtures, mocks, assertions, and test-only configuration | Faithful tests with focused and full validation evidence |
| [`mule-troubleshooting`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-troubleshooting) | Incidents, timeouts, connection failures, rate limits, concurrency, memory, cross-application failures | Root-cause assessment or fix plan; no source change unless requested |
| [`mule-ops`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-ops) | Runtime health, deployments, logs, metrics, recurring checks, multi-application correlation | Evidence-backed operational assessment |
| [`mule-review`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-review) | Working changes, commits, branches, PRs, whole projects, release readiness | Prioritized findings and fix options; no implementation or PR-state change unless requested |
| [`mule-build`](https://github.com/Avinava/mule-skills/tree/main/skills/mule-build) | Validation, tests, packaging, and explicitly requested release actions | Deployable artifact and validation summary |

## Choosing the right skill

| Request | Start with | Add when needed |
| --- | --- | --- |
| Explain or refresh the project | `mule-docs` | Optional business-context questions when source cannot establish purpose or ownership |
| Implement a change | `mule-development` | Documentation refresh, then change review |
| Add or repair MUnit tests | `mule-testing` | `mule-build` for execution; development if a product defect is exposed |
| Diagnose a symptom | `mule-troubleshooting` | `mule-ops` for authorized runtime evidence; development only when a fix is requested |
| Assess current runtime health | `mule-ops` | `mule-troubleshooting` when a specific causal question emerges |
| Review a change or repository | `mule-review` | `mule-ops` only for authorized, material runtime verification |
| Prepare a release | `mule-build` | Release-readiness review before commit, tag, publish, or deploy |

## What they read

Every skill reads `AGENTS.md` for shared project context, which is why
[project setup](project-setup.md) matters more than the install itself. Skills refer to their bundled
references and scripts through `<skill-root>` and `<skills-root>` placeholders, so the same file works
under a plugin install and a vendored install.

Documentation and review questions are optional and non-blocking. When business information would
materially improve the result, the skill offers concise choices plus `Other` and `Not sure / Skip`,
then continues with verified technical evidence if you skip.

## Runtime evidence is gated, not assumed

`mule-ops`, `mule-troubleshooting`, `mule-review`, and the publish and deploy actions in `mule-build`
confirm Anypoint access before their first connector call, and offer setup, supplied exports, or a
repository-only scope when it is missing. See [Anypoint access](anypoint-access.md).

## Example prompts

```text
Use mule-docs to refresh architecture and operations documentation. Ask optional business questions
with choices where the repository cannot establish important context.

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
