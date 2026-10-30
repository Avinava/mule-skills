<div class="hero" markdown>

![Mule Skills: agent skills to design, develop, test, review, release, and operate Mule 4 apps](assets/banner.svg){ width="760" }

# Give your coding agent a MuleSoft engineering playbook

Mule Skills helps Codex, Claude, Copilot, Gemini, Cursor, and similar agents work with Mule 4
projects using the same lifecycle your team already knows: design, develop, test, package, review,
release, operate, and troubleshoot.

[Install in a Mule project](getting-started.md){ .md-button .md-button--primary }
[See it in action](see-it-in-action.md){ .md-button }

</div>

No agent replaces Anypoint Studio, Maven, MUnit, or your review process. The skills tell the agent
how to inspect current-project evidence, choose the right tool, validate proportionately, and stop
before a mutation that needs your approval.

<div class="path-grid" markdown>

<div class="path-card" markdown>

### MuleSoft developer

Describe the change in Mule terms. The agent routes between API design, Mule XML/DataWeave,
documentation, MUnit, build, and review.

[See a developer change](see-it-in-action.md)

</div>

<div class="path-card" markdown>

### Test or release engineer

Use behavior-focused MUnit guidance, repeatable build gates, artifact evidence, a written rollback
plan, and a separate approval boundary for Anypoint publishing or deployment.

[Follow a workflow](workflows.md)

</div>

<div class="path-card" markdown>

### Platform or support engineer

Analyze runtime health and incidents from authorized Anypoint evidence or supplied exports without
turning missing telemetry into a confident conclusion.

[Understand Anypoint access](anypoint-access.md)

</div>

</div>

## See the outputs

Four concrete examples show a change with test evidence, a prioritized review finding,
source-grounded documentation, and a locally validated API contract.

<div class="showcase-grid" markdown>

<div class="showcase-card" markdown>

[![Development evidence and release-readiness verdict](assets/showcase/development.png)](see-it-in-action.md#journey-1-make-a-small-mule-change-and-prove-what-is-ready)

**Change, test, and package.** A currency change, passing tests, and a lint-gated verdict.

</div>

<div class="showcase-card" markdown>

[![Review finding with impact and remediation](assets/showcase/review.png)](see-it-in-action.md#journey-2-review-a-deliberately-flawed-mule-project-without-changing-it)

**Find release risks.** A missing error handler becomes a prioritized finding.

</div>

<div class="showcase-card" markdown>

[![Architecture and flow catalog derived from sample source](assets/showcase/documentation.png)](see-it-in-action.md#journey-3-document-the-sample-project)

**Document a project.** What each flow does, and what the source does not establish.

</div>

<div class="showcase-card" markdown>

[![RAML contract and local validation evidence](assets/showcase/api-design.png)](see-it-in-action.md#journey-4-design-an-orders-api)

**Design an API.** A consumer requirement becomes a validated RAML contract.

</div>

</div>

These are rendered artifact captures. The development and review examples retain their recorded
2026-10-27 evidence; documentation and API design were produced on 2026-10-30.
[Read the prompts, sources, and limitations](see-it-in-action.md).

## The Mule lifecycle, with clear ownership

```mermaid
flowchart LR
    D[Design<br/>mule-api-design] --> I[Implement<br/>mule-development]
    I --> T[Test<br/>mule-testing]
    T --> B[Check and package<br/>mule-build + mule-lint]
    B --> R[Review<br/>mule-review]
    R --> A[Release and deploy<br/>mule-ops + anypoint-connect]
    A --> O[Operate<br/>mule-ops]
    O --> X[Troubleshoot<br/>mule-troubleshooting]
    Docs[mule-docs] -. refreshes evidence .-> D
    Docs -.-> I
    Docs -.-> O
    Conn[mule-connectors] -. connector facts .-> I
    Deps[mule-dependencies] -. versions .-> I
```

`mule-build` owns local checks, MUnit execution, packaging, local runtime work, and version/tag
preparation. `anypoint-connect`, used through operational workflows, owns explicitly approved
Exchange publishing and Anypoint runtime changes. [See the complete ownership map](ecosystem.md).

## Paste one instruction

Open your Mule repository in the agent and paste:

```text
Fetch and follow https://raw.githubusercontent.com/Avinava/mule-skills/main/docs/agent-install.md
to install or update Mule Skills in this Mule repository. Detect the agent host and existing
configuration, preview the changes, preserve customized files, run the validation, and do not
commit or authenticate to Anypoint unless I approve it.
```

The agent inspects first, detects an existing install, previews file and MCP changes, avoids
duplicate configuration, installs all ten skills, validates the result, and leaves commit and
authentication decisions with you. [Walk through the result](getting-started.md).

## What gets installed

| Layer | Purpose | Credentials |
| --- | --- | --- |
| Ten `mule-*` skills | Decide how to design, implement, test, document, build, review, release, operate, diagnose, answer connector questions, and keep dependencies current | None |
| `mule-lint@2.3.0` | Mule standards, static analysis, XML formatting, RAML/OAS validation | None |
| `mule-build@3.2.0` | Readiness, MUnit, package, local runtime, version and tag preparation | None |
| `anypoint-connect@0.17.0` | Authorized Design Center, Exchange, Governance, telemetry, and lifecycle actions | Anypoint login only when needed |

Use Node.js `>=22.0.0` for the MCP servers; Node.js 24 LTS is recommended. The skills
themselves are instructions and remain useful when an MCP server is unavailable; the missing tool
becomes a visible validation gap.

## Safety you can predict

| Request | Default behavior |
| --- | --- |
| Review or diagnose | Read-only findings; no source or PR changes |
| Develop or repair tests | Implement only the requested scope and run focused plus proportionate checks |
| Build | Validate, run MUnit, and package; no version, tag, publish, or deploy |
| Release preparation | Preview/check first; version, commit, or push only when explicitly requested; tag after production proves the release |
| Publish, deploy, restart, scale, or rollback | Separate Anypoint scope, readiness probe, and explicit approval |

Project facts stay in the Mule repository's `AGENTS.md`; reusable skill files stay neutral. Private
hosts, tenant identifiers, credentials, payloads, and customer fingerprints do not belong in either
the reusable bundle or examples.
