---
name: mule-dependencies
description: Look up the current release, minimum Mule runtime, and Java support of Mule connectors, modules, MUnit, and the Mule Maven plugin, and check a project's dependencies for upgrades. Use when asked for the latest connector or plugin version, whether a connector works with a Mule runtime or Java version, which Java a runtime channel supports, or which dependencies in a pom are outdated. Never answer a version question from memory. Route applying the upgrade to mule-development and build verification to mule-build.
---

# Mule Dependencies

Answer version and compatibility questions from a live lookup, not from memory. Connector releases,
runtime channels, and Java support change monthly, and several public sources return stale or
misleading answers.

## Look up, then answer

Run the bundled script. It never changes project files, uses the standard library only, and prints
JSON on stdout. It caches responses under the user cache directory (`$XDG_CACHE_HOME` or
`~/.cache`); pass `--no-cache` to bypass it or `--offline` to read only the bundled snapshot:

```bash
python3 <skill-root>/scripts/mule_versions.py connector salesforce sftp --mule 4.9.0 --java 17
python3 <skill-root>/scripts/mule_versions.py plugins
python3 <skill-root>/scripts/mule_versions.py runtime
python3 <skill-root>/scripts/mule_versions.py notes salesforce --grep "client credentials"
python3 <skill-root>/scripts/mule_versions.py check <project-root>/pom.xml
```

`<skill-root>` is `${CLAUDE_PLUGIN_ROOT}/skills/mule-dependencies` for the Claude plugin and
`.agents/skills/mule-dependencies` when vendored into a project.

- `connector` takes an alias (run with an unknown name to list them) or `group:artifact`. Without
  `--mule` and `--java` it reports the newest release only. With them it also reports the newest
  release that satisfies both.
- `check` reads `mule-plugin` dependencies and the build plugins from the pom, resolves version
  properties, and takes `minMuleVersion` from the sibling `mule-artifact.json` and the Java level from
  pom properties. Pass `--mule` or `--java` to override.
- `notes` reads the connector's MuleSoft release-notes page and returns each version's date,
  minimum Mule version and Java levels. With `--grep` it returns only the versions that mention the
  term, with snippets, anchors and `earliestMatch`. Use it for "which version added or removed this
  feature or connection type" instead of answering from memory. `--url` takes a
  `docs.mulesoft.com` page for a connector without a known page. The result's `coverage` gives the
  oldest version on the page: a match at that version is a lower bound, because older releases can
  sit on an archived page. A mention can be a fix or a removal, so read the snippet before claiming
  when a feature arrived.
- Every result carries `source` and `fetchedAt`. Quote them when you report a version.

When the user is logged in to Anypoint, the anypoint-connect `get_exchange_asset` tool returns the
same Exchange data and also covers private organization assets. Prefer it for private assets; use the
script for public MuleSoft artifacts and for pom checks.

## Exit codes and fallbacks

| Exit | Meaning | What to do |
| --- | --- | --- |
| 0 | Answer produced | Report it with source and time; surface `warnings` |
| 2 | Unknown alias, artifact not found, or no release satisfies the constraints | Say so; do not substitute a nearby version |
| 2 | `notes --grep` found no mention | Say the page does not mention it; it is not proof the feature is absent |
| 3 | Network or authentication failure | Fetch the URL named in the error with the agent's web fetch tool when one is available; otherwise report that live verification failed and offer `--offline` (not for `notes` or `check`) |
| 64 | Usage error | Fix the command |

`--offline` reads a dated snapshot bundled with the skill. Treat its answers as unverified, say
"as of" the snapshot date, and recommend re-running online. `--refresh-snapshot` rebuilds the
snapshot from live sources; run it only when maintaining this skill.

## Gotchas

- Never take Mule versions from Maven Central. It holds only old uploads and answers with a valid
  but badly outdated version without any error.
- A repository `latest` tag can be a `-DEV`, `-SNAPSHOT`, `-RC`, or milestone build. The script
  filters those; do the same when reading metadata by hand.
- A newer connector can require a newer runtime or drop older Java levels. Select by the project's
  runtime and Java, not by the highest number.
- Source differences matter: only Exchange reports minimum runtime and Java support. Results from
  Maven sources say `unknown` for compatibility; verify those before recommending.
- The runtime table covers Java support only. Support end dates change, so send the user to the
  support policy page the script returns instead of quoting dates.
- Enterprise-only repositories need credentials. Report an authentication failure; do not guess.

## Report

State, for each dependency: current version if known, newest release, newest compatible release, the
constraints used, source, and fetch time. Mark anything unverified. Recommend upgrades only when a
compatible newer release exists, and hand the change to `mule-development` and verification to
`mule-build`. See [sources and failure modes](references/sources.md) when a lookup disagrees with
another source or fails unexpectedly.
