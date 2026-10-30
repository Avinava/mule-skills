<p align="center">
  <img src="docs/assets/banner.svg" alt="Mule Skills: evidence-backed MuleSoft agent workflows from design to release and operations" width="960" />
</p>

<p align="center">
  <strong>Reusable AI-agent workflows for the Mule 4 engineering lifecycle.</strong>
</p>

<p align="center">
  <a href="https://avinava.github.io/mule-skills/">Documentation</a> ·
  <a href="https://avinava.github.io/mule-skills/see-it-in-action/">See it in action</a> ·
  <a href="https://avinava.github.io/mule-skills/anypoint-access/">Anypoint access</a> ·
  <a href="https://avinava.github.io/mule-skills/faq/">FAQ</a>
</p>

Mule Skills gives coding agents a shared way to document, develop, test, build, troubleshoot, operate, and review
MuleSoft projects. The workflows start from current-project evidence, keep business context separate
from implemented behavior, and avoid carrying identity or tuning assumptions between projects.

The skills work as instruction-only workflows and can use the included MCP configurations when
local build, lint, or authorized Anypoint evidence is available.

## Install

### Tell your AI agent

**Codex / Claude Code / GitHub Copilot / Gemini / Cursor:**

```text
Fetch and follow https://raw.githubusercontent.com/Avinava/mule-skills/main/docs/agent-install.md
to install or update Mule Skills in this Mule repository. Detect the agent host and existing
configuration, preview the changes, preserve customized files, run the validation, and do not
commit or authenticate to Anypoint unless I approve it.
```

That is enough. The runbook detects whether this is a new install or upgrade, selects the right
host configuration, previews changes, installs all ten skills, and verifies what landed.

For Claude Code, install the plugin directly:

```text
/plugin marketplace add Avinava/mule-skills
/plugin install mule-skills@mule-skills
```

For details, use the [Claude Code plugin guide](docs/install-claude-code.md)
or [other-agent installer](docs/install-other-agents.md).
Then [set up your project context](docs/project-setup.md).

## See it in action

<table>
  <tr>
    <td width="50%"><a href="docs/see-it-in-action.md#journey-1-make-a-small-mule-change-and-prove-what-is-ready"><img src="docs/assets/showcase/development.png" alt="DataWeave change, MUnit evidence, and release-readiness handoff"></a><br><b>Change, test, and package.</b> Full tests and packaging passed; lint findings still block release readiness.</td>
    <td width="50%"><a href="docs/see-it-in-action.md#journey-2-review-a-deliberately-flawed-mule-project-without-changing-it"><img src="docs/assets/showcase/review.png" alt="Review finding with missing error handler, impact, and remediation"></a><br><b>Find release risks.</b> A missing error handler becomes a prioritized finding with a source location and fix direction.</td>
  </tr>
  <tr>
    <td width="50%"><a href="docs/see-it-in-action.md#journey-3-document-the-sample-project"><img src="docs/assets/showcase/documentation.png" alt="Sample architecture and source-backed flow catalog"></a><br><b>Document a project.</b> Trace the request through the implementation and see what each flow does.</td>
    <td width="50%"><a href="docs/see-it-in-action.md#journey-4-design-an-orders-api"><img src="docs/assets/showcase/api-design.png" alt="Orders API RAML excerpt and local validation evidence"></a><br><b>Design an API.</b> Turn consumer requirements into an explicit contract and inspect its validation evidence.</td>
  </tr>
</table>

<details>
<summary>Prompts behind these examples</summary>

```text
Add currency: "USD" to the sample order response, extend its MUnit test,
validate and package, then review the result. Do not commit or deploy.
```

```text
Review this Mule application for correctness and release risk.
Report findings and fix directions without editing files.
```

```text
Use mule-docs to document the sample application's architecture and flows.
Distinguish implemented behavior from assumptions and missing evidence.
```

```text
Use mule-api-design to design a RAML 1.0 order lookup API with
explicit responses and local validation. Do not publish.
```

</details>

These captures show rendered sample artifacts. The [walkthrough](docs/see-it-in-action.md) distinguishes
recorded tool evidence, representative handoffs, and fresh examples.

## Skills

| Skill | Use it for |
| --- | --- |
| [`mule-api-design`](skills/mule-api-design/) | HTTP API workshops, URI/method/data/error design, RAML/OAS authoring, contract assessment, and safe Design Center workflows |
| [`mule-docs`](skills/mule-docs/) | Project documentation, architecture, APIs, flows, onboarding, operations, and targeted refreshes |
| [`mule-development`](skills/mule-development/) | Mule production XML, DataWeave, APIKit implementation, connectors, error handling, queues, batch, and configuration |
| [`mule-testing`](skills/mule-testing/) | Behavior-focused MUnit authoring, repair, fixtures, mocks, assertions, and test-only configuration |
| [`mule-troubleshooting`](skills/mule-troubleshooting/) | Incidents, timeouts, connection failures, rate limits, concurrency, memory, and cross-application failures |
| [`mule-ops`](skills/mule-ops/) | Runtime health, releases and hotfixes, deployments, logs, metrics, recurring checks, and multi-application correlation |
| [`mule-review`](skills/mule-review/) | Working changes, commits, branches, PRs, whole projects, and release readiness |
| [`mule-build`](skills/mule-build/) | Local validation, tests, packaging, runtime work, versioning, and tags |
| [`mule-dependencies`](skills/mule-dependencies/) | Latest and compatible connector, plugin, and runtime versions, release-note feature lookups, and pom upgrade checks |
| [`mule-connectors`](skills/mule-connectors/) | Connector authentication by version, token rules, run-as identity, subscription sources and replay, benign signatures, and sensitive loggers |

See the [skill catalog](docs/skills.md) for routing and expected handoffs, or
[workflow examples](docs/workflows.md) for more copyable prompts.

## MCP support

Credential-free launch configuration for three pinned MCP servers:

| Server and source | Exact package pin | Role |
| --- | --- | --- |
| [`anypoint-connect`](https://github.com/Avinava/anypoint-connect) | [`@sfdxy/anypoint-connect@0.17.0`](https://registry.npmjs.org/@sfdxy%2Fanypoint-connect/0.17.0) | Authorized Design Center, Exchange, Governance, runtime evidence, and lifecycle operations |
| [`mule-build`](https://github.com/Avinava/mule-build) | [`@sfdxy/mule-build@3.2.0`](https://registry.npmjs.org/@sfdxy%2Fmule-build/3.2.0) |
| [`mule-lint`](https://github.com/Avinava/mule-lint) | [`@sfdxy/mule-lint@2.3.0`](https://registry.npmjs.org/@sfdxy%2Fmule-lint/2.3.0) |

Source links come from each published package's repository metadata. Package links resolve to the
exact registry version used by the checked-in configuration rather than an unpinned latest release.
Node.js `>=22.0.0` satisfies all three. Node.js 24 LTS is recommended for a new installation.

`mule-build` and `mule-lint` need no credentials. `anypoint-connect` idles until you authenticate;
see [docs/anypoint-access.md](docs/anypoint-access.md).

For host configuration and capability checks, see [MCP servers](docs/mcp-servers.md)
and [Anypoint access](docs/anypoint-access.md).

## Documentation

- [Getting started](docs/getting-started.md) and [project setup](docs/project-setup.md)
- [Four worked examples](docs/see-it-in-action.md)
- [Workflow guide](docs/workflows.md) and [FAQ](docs/faq.md)
- [Tool ownership and compatibility](docs/ecosystem.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository structure, skill conventions,
and required checks. Release history is in [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
