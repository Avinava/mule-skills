# Safe change to a running application

## Contents

- [When to use](#when-to-use)
- [Before the change](#before-the-change)
- [Choose the deployment mode](#choose-the-deployment-mode)
- [Apply the change](#apply-the-change)
- [After the change](#after-the-change)
- [Report](#report)

## When to use

Read this when the user has authorized a change to a deployed application: a new artifact
version, a property or secret change, a runtime upgrade, a switch of authentication flow or
integration user, or a first start of an app in a new environment. It complements
[Artifact identity handoff](../../mule-build/references/artifact-handoff.md), which covers what is
deployed; this covers how to change it without losing or duplicating work. Analysis alone never
authorizes a change. Confirm the environment, and its production flag, before any write.

## Before the change

1. **Find the real source of truth.** Compare what is deployed with the repository:
   `compare_deployed_artifact(appName, environment, against: {repoPath, gitRef, includeWorkingTree})`.
   A deployed JAR can carry changes that were never committed, such as a mapping or a contract
   edit. When it differs, reconcile into the repository first, or the change silently reverts
   production behavior. Without the tool, download the deployed artifact and diff its
   `src/main/mule` and `src/main/resources` equivalents by hand.
2. **Check the environment boundary.** A non-production app can still reach a live system: an
   endpoint hard-coded in XML, a non-production properties file pointing at a production tenant, or
   a shared credential. Before any local run, non-production start or first deployment, list every
   outbound endpoint per environment and flag any that resolve to a production or customer-live
   system. Then keep schedulers and pollers from firing against it: stop those flows, disable them
   through configuration, or start the app outside their windows.
3. **Check what depends on the identity.** When the integration user or the authentication flow
   changes, the target system sees a different user. List what keys off that user before switching:
   validation or business rules on the user's profile or role, automation that reads running-user
   fields, record owner and created-by on new records, sharing, permission assignments, and audit
   reports filtered by user. Connector-side state can depend on it too: a subscription's stored
   resume position may be keyed on the configured user. Connector profiles in `mule-connectors`
   name the target's mechanisms.
4. **Check how secrets are supplied.** Confirm each changed secret's supply model and placeholder
   ([secret supply models](../../mule-development/references/secrets-and-tls.md#secret-supply-models)).
   Read current settings with `get_app_settings`; a secret-looking key stored as a plaintext
   property is a finding to fix in the same change.
5. **Check versions.** The connector version must support the connection type in use
   (`mule-connectors`, then `mule-dependencies`), and the runtime must still be offered on the
   target (`list_runtime_versions`).

## Choose the deployment mode

| The app has | Use | Why |
| --- | --- | --- |
| Subscription, streaming or polling sources, or schedulers | `mode: stopStart` for the change, and `updateStrategy: recreate` persisted on the app | Old and new replicas never process events together. A rolling update processes every event of the overlap twice |
| Only request-driven listeners | Default in-place (rolling) update | No downtime; requests drain normally |
| A replay position held in memory only | Stop-start, then confirm the start position | A "new events only" start loses everything published while stopped |

Both no-overlap options were measured on a CloudHub 2.0 shared-region sandbox (runtime 4.9, Java
17, 2026-10-26) with a probe whose scheduler logs its generation and pod every second. Gap is the
time from the old generation's last tick to the new one's first; negative means both ran:

| Mode | 1 replica | 2 replicas |
| --- | --- | --- |
| Rolling | -7 s (overlap) | -32 s (overlap) |
| Recreate (property change or artifact version bump) | +108 s | +110 to +112 s |
| `stopStart` | +58 s | +57 s |

- Recreate never overlapped, whether it was set in the same update or already persisted, for a
  property change and for an artifact version bump. It is documented for CloudHub 2.0
  ([updates](https://docs.mulesoft.com/cloudhub-2/ch2-update-apps)).
- `stopStart` gave about half the downtime of recreate. Prefer it for a change you make now.
- Recreate is a persistent app setting, so it also protects later deployments made from Runtime
  Manager or a pipeline that would otherwise default to rolling. Set it on every subscription app.
- Rolling overlap grows with replica count. Scaling the replica count under rolling also replaced
  the running pod with an overlap, so treat a scale operation as a deployment.
- These are single measurements on one target and runtime. Re-measure on a private space or Runtime
  Fabric before relying on the numbers there.

Read the replay and duplicate rules in Class E
([Subscription sources](../../mule-development/references/invariant-classes.md#subscription-sources))
before changing a subscription app.

## Apply the change

- Make the whole change one previewed update: `update_app` with the version, runtime, settings and
  mode together. Read the preview's steps and diff, then confirm. Production needs its own explicit
  confirmation.
- Supply secret values from a file or environment variable source (`securePropertiesFrom`), and
  move existing plaintext secrets with `moveToSecure`, so no value enters the conversation.
- Let the tool wait until every replica runs the new spec. A start-up `FAILED` before replicas
  settle is not yet a failure; judge the settled phase.

## After the change

1. **Prove the identity and the flow.** Confirm from the target system which user logged in and by
   which flow, and confirm the token's identity with the target's identity call. Do not infer it
   from configuration: the run-as user can be changed on the client application without a code
   change. Connector profiles list the exact queries.
2. **Smoke-test without side effects.** Send a probe that exercises the real path but stops at a
   guard: an event whose precondition check finds nothing to do, or a request for a record whose
   parent does not exist so the target rejects it on its own referential rule. That proves
   connectivity, authentication and routing with nothing written. For managed HTTP APIs,
   `smoke_test_api` sends one request with the API's client credentials scrubbed from the output.
3. **Read logs against known signatures.** Check `get_logs` for the start-up window. Classify
   connector lines against the profile's known signatures before counting errors, and confirm a
   benign signature still meets its criteria (for example, events keep arriving after a periodic
   reconnect).
4. **Watch the first reconnect.** For long-lived subscriptions, confirm the first reconnect after
   the change renews credentials and resumes, before calling the change done.
5. **Never raise sensitive loggers.** If more logging is needed, check the profile's sensitive
   loggers first; some connector categories write session identifiers at DEBUG.

## Report

State what changed, the mode used and why, the source-of-truth comparison result, the boundary and
identity checks with their results, the smoke probe and its guard, and anything left unverified.
Never include property values, tokens, user names or endpoint hosts.
