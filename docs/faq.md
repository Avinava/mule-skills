# FAQ and setup troubleshooting

## Install and discovery

**The agent does not pick up a skill.** Confirm discovery first, then routing. Under Claude Code,
`/plugin` should list `mule-skills` as enabled. Under any other host, `.agents/skills/<name>/SKILL.md`
must exist and the host's instruction file must point at `.agents/skills/`. If both are true, name the
skill explicitly — `use mule-review …` — and check that the request looks like the skill's trigger
description.

**Should I use the plugin or the installer?** Claude Code should use the plugin: skills and MCP
configuration come with it and nothing is copied into your project. Every other host uses
[`install/install.sh`](https://github.com/Avinava/mule-skills/blob/main/install/install.sh), which
vendors the skills into `.agents/skills/`. Installing both in one project means two copies of the
same skills, which is why the installer warns when it detects Claude Code.

**Will the installer overwrite my files?** Skills under `.agents/skills/` are replaced on every run.
Everything else is only added when missing. `AGENTS.md` is never overwritten, not even with
`--force`, because it holds context you wrote. Use `--dry-run` to see the plan first.

**I renamed or upgraded from an older version.** The installer and the agent-driven install both
remove the superseded `document-mulesoft-project`, `review-mulesoft-project`, and
`.agents/workflows/build.md` paths. Update saved prompts that still name them.

**Do I still need `CLAUDE.md`?** Not for routing. You do want an `AGENTS.md` with this project's
evidence-backed context — see [project setup](project-setup.md).

## MCP servers

**A server does not connect.** Check Node.js: all three need `>=20.19.0`. Then verify the host sees
it — `/mcp`, `codex mcp list`, `copilot mcp list`, or the host's MCP view. VS Code needs a window
reload after its configuration changes.

**The first call hangs for a while.** That is `npx` downloading a pinned package on a cold start. It
happens once per server per cache.

**The installer skipped my VS Code configuration.** `.vscode/mcp.json` accepts comments and trailing
commas, which a strict JSON parser cannot read. The installer reports the skip and names the servers
so you can add them by hand rather than corrupting the file.

**My Codex configuration broke after a merge.** Codex accepts `[mcp_servers.name]`,
`[mcp_servers."name"]`, and an inline table. The installer detects all three before appending, so a
duplicate table should not happen; if one exists, remove the duplicate and re-run.

**Can I run without any MCP server?** Yes. The skills are instruction-only workflows. Missing tooling
becomes a disclosed coverage gap.

## Anypoint access

**I asked for logs and the agent asked me to set something up.** Runtime evidence needs the
authenticated `anypoint-connect` server. The skill probes for access first and offers you setup,
supplied exports, or a repository-only scope. Full detail in [Anypoint access](anypoint-access.md).

**`whoami` works but my environment is missing.** Authentication succeeded against a different
organization, business group, or profile than the one holding that environment. Check the active
profile with `anc config use` and confirm the environment name spelling.

**My session expired mid-analysis.** Run `anc auth login` again, then ask the agent to re-confirm
access. Telemetry already collected keeps its stated coverage; do not extend a conclusion past it.

**I would rather not authenticate.** Supply exports instead. Say which application, environment,
window, timezone, and log level they cover, and whether the export was truncated — that metadata is
what decides how far a conclusion can go.

**Will the agent deploy something while checking access?** No. Readiness uses read-only identity and
environment calls, and every mutating operation needs explicit authorization.

## Working with the skills

**A report says `Unresolved` instead of giving me an answer.** That is deliberate. Missing coverage
stays visible rather than becoming a confident claim. The report names the discriminating check that
would resolve it.

**Can I get a number for concurrency, pool size, or a timeout?** Only with measured traffic, replica
count, and dependency capacity for your environment. The skills do not carry tuning values between
projects.

**Why does a review not fix what it finds?** Review and diagnosis are read-only by default. Ask for
implementation explicitly, and `mule-development` or `mule-build` takes over.

**Where do I report a problem or contribute?** Open an issue or pull request on
[GitHub](https://github.com/Avinava/mule-skills). Contribution rules and the required validation
commands are in the repository README.
