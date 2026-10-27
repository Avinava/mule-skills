---
name: mule-connectors
description: Answer connector-specific behavior questions in Mule 4: which connection types and authentication flows a connector version supports, token and endpoint rules, the run-as identity, account or licence limits, subscription sources and replay, reconnect and token renewal, log signatures that are benign, and logger categories that leak credentials. Use for questions such as moving a Salesforce integration to OAuth client credentials, choosing a streaming replay option, switching an integration user, or deciding whether a connector log error matters. Uses a curated connector profile when one exists and builds one from live MuleSoft sources when it does not. Read-only: route version lookups to mule-dependencies, source changes to mule-development, incident triage to mule-troubleshooting, and deployment changes to mule-ops.
---

# Mule Connectors

Connector behavior changes by version, and the errors a connector raises rarely say which version
you need. Answer from a profile whose claims carry evidence, never from memory.

## Privacy and reuse boundary

- Profiles hold connector facts only. Never write an organization, tenant, application, flow,
  user, host or environment name into a profile, an example or a report.
- Describe a field observation by its setting: "observed on a non-production app over two days on
  connector 11.x", never by the app or user that showed it.
- Never copy tokens, session identifiers, client secrets or consumer keys from logs into any output.

## Workflow

### 1. Find or build the profile

Look for `references/<connector>.md`. Curated profiles exist for:

| Connector | Profile |
| --- | --- |
| Salesforce | [references/salesforce.md](references/salesforce.md) |

A profile is a starting point. Re-verify every row the answer depends on (step 2). When no profile
exists, build a transient one with the same sections from live sources:

1. Versions, minimum Mule version and Java levels:
   `mule-dependencies/scripts/mule_versions.py connector <name> --mule <x> --java <n>`.
2. Which version added, changed or removed a feature or connection type:
   `mule_versions.py notes <name> --grep "<term>"`. Quote `earliestMatch` with the page `coverage`;
   a match at the oldest version on the page is a lower bound.
3. Connection types, sources and parameters for the exact version: the connector reference page on
   `docs.mulesoft.com` (`<connector>/latest/<connector>-reference`, or the versioned page). When the
   plugin jar is in the local Maven repository, its `META-INF/mule-artifact/mule-artifact.json`
   confirms which version resolved.
4. When the script cannot reach the network (exit 3, or a proxy or sandbox refusal), do not stop.
   The error names the URL it tried: fetch that same `docs.mulesoft.com` page with the agent's web
   fetch tool and apply the same reading rules (version headings, compatibility table, coverage).
   Only when every route fails, answer from the profile and say which rows were not re-verified.
5. Behavior the documentation does not state, such as token renewal across reconnects or which
   log lines are benign: mark it `Unverified` and say how to observe it on a non-production app.

Offer a transient profile as a new `references/<connector>.md` only when the user asks, after a
pass that removes every project, organization and person identifier.

### 2. Check the claims the answer uses

Every profile row has this shape:

| Claim | Versions | Evidence | Re-verify by |
| --- | --- | --- | --- |
| What is true | Range it holds for | `Documented: <URL>` or `Observed: <setting, date, version>` | The lookup or check that confirms it now |

- Re-verify at least the rows the answer's decision rests on (the version that adds or removes a
  connection type, and its runtime and Java needs) with a live source in this session, using the
  web-fetch fallback when the script is blocked.
- `Documented` rows: re-run the lookup in "Re-verify by" when the project's connector version is
  outside the stated range, or when the profile's `verified` date is older than the latest release.
- `Observed` rows: state them as observed, with the setting. Do not promote them to documented.
- When a live lookup contradicts a profile row, the live result wins. Say so and propose the
  profile fix.

### 3. Apply the profile

Each profile has these sections. Use the ones the question touches:

| Section | Answers |
| --- | --- |
| Connection types by version | Which authentication flows a version supports, and what a version removed |
| Token and endpoint rules | Which token URL or host a flow requires |
| Run-as identity | Where the effective user is configured and how to prove it from a token |
| Account and licence limits | Which account types cannot use which flows |
| Sources | Subscription semantics, replay options, reconnect and token renewal |
| Known signatures | Log lines that are benign, and the criteria under which they stop being benign |
| Sensitive loggers | Logger categories that write credentials or session identifiers at DEBUG or TRACE |
| Identity verification | Queries that prove which identity and which flow logged in |
| Non-blocking warnings | Messages that look alarming but do not stop the connection |

Then hand off:

- Version choice and upgrades: `mule-dependencies` for the lookup, `mule-build` for verification.
- Configuration and source changes: `mule-development`, including
  [secret supply models](../mule-development/references/secrets-and-tls.md#secret-supply-models) for
  where the client secret comes from.
- Changing a running app, the integration user or a subscription source:
  [safe change](../mule-ops/references/safe-change.md) in `mule-ops`.
- A connector error in an incident: `mule-troubleshooting`, after checking the profile's known
  signatures.

## Report

For each claim: the claim, its version range, its evidence state with the URL or observation
setting, and whether it was re-verified in this session. Keep unverified and observed claims
visibly separate from documented ones.

## Gotchas

- A connector error naming a missing parameter or element often means the connection type does not
  exist in that version at all. Check connection types by version before debugging configuration.
- Release notes list fixes and removals as well as additions. Read the snippet before saying a
  feature "arrived" in a version.
- A connector major can drop a connection type or Java level outright, and apps using it fail to
  deploy. Check the target major's "What's New" before an upgrade.
- The identity a token belongs to can change outside the code, for example when an administrator
  changes the run-as user on the client application. Verify identity from the token, not from
  configuration.
- Raising a connector's internal logger to DEBUG can write session identifiers or tokens to logs
  that other people can read. Check the profile's sensitive loggers first.
