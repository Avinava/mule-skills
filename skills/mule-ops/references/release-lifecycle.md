# Release lifecycle

## Contents

- [When to use](#when-to-use)
- [Before the release](#before-the-release)
- [Hotfixes](#hotfixes)
- [Apply](#apply)
- [Watch](#watch)
- [Healthy, defined positively](#healthy-defined-positively)
- [Roll back or hold](#roll-back-or-hold)
- [Hypercare](#hypercare)
- [Tag the release](#tag-the-release)

## When to use

Read this when an authorized change will reach a shared or production environment: a release, a
hotfix, a rollback, or a property change. [Safe change](safe-change.md) covers how to apply one
change without losing or duplicating work; this file covers the release around it: what to record
first, how to watch, when to call it healthy, and when to tag. Analysis never authorizes a mutation.

## Before the release

1. **Record what runs now.** `get_deployment_spec` returns the artifact reference, runtime patch
   version, replica count, update strategy, and the desired and last-successful versions. Record the
   running artifact by full name and SHA-256. It is the first rollback target, and the recorded
   runtime patch is how a later silent platform patch becomes visible.
2. **Read the effective configuration.** Platform properties override the packaged files, so the
   repository is not the running configuration. Read `get_app_settings` before reasoning from
   property files. A stale platform property keeps overriding until it is removed or the code stops
   reading the key.
3. **Diff every key the candidate reads against what the target supplies.** Cover the packaged
   files, the encrypted secure file, and the platform properties. New keys, and keys that moved
   between `${secure::key}` and `${key}`, pass every environment that happens to supply them and
   fail to start where none does. The mule-lint placeholder checks find the keys; the diff against
   the target is still yours.
4. **Use the production build path.** A build that strips secure prefixes for a local or sandbox run
   cannot start where the value is only available as a secure property. mule-build marks such a jar
   as not production-deployable; never deploy one to production.
5. **Check selectors against real data.** A filter on a status, type or picklist value must use the
   value production writes, not a field default. Query recent production records and run the exact
   query the release adds before it ships.
6. **Write the rollback plan.** Name the target artifact by full name and digest, and whether rolling
   back needs a property write; prefer a target that needs none. Keep a never-deploy list:
   superseded builds of the same version, withdrawn assets, and targets that predate a property or
   credential the environment now requires. Production changes verify the rollback target's build
   marker too: a target without one needs an unmarked-artifact allowance, so settle that now
   ([Anypoint access](anypoint-readiness.md#consent-and-privacy)).
7. **State the accepted loss.** Every start loses something
   ([what a start loses](safe-change.md#what-a-start-loses)). Write down what this start will lose
   and how it will be reconciled before applying it.

## Hotfixes

- **Branch from the running artifact's source.** Production can run a build that has no tag. Find
  the commit that built it, prove it by comparing the artifact with that commit
  (`compare_deployed_artifact`), and branch from there, not from the default branch.
- **Version with a qualifier.** Use a semantic prerelease qualifier such as `1.4.2-hotfix.1`. The
  Mule Maven plugin rejects four-part versions such as `1.4.2.1`. mule-build's `release_version`
  produces it with `bump: "prerelease"` and `preid: "hotfix"`. It commits, tags and pushes by
  default when confirmed, so pass `noTag: true` and `noPush: true` unless the user asked for them;
  the tag comes after production proves the release.
- **Diff the hotfix artifact against the running one.** Only version metadata and the files you
  meant to change may differ. Anything else is an unreviewed change.

## Apply

- **A property write is a full redeploy.** Treat a one-line flag change as a release: same mode
  choice, same watch, same rollback plan. Put the artifact and all its properties in one
  `update_app` so the app starts once.
- **Approve mutating calls.** `update_app`, `update_app_settings`, `deploy_app`, `deploy_jar`,
  `restart_app`, `rollback_app` and `scale_app` change a running app. By default the host asks for
  each call, and production also needs the user's confirmation unless the user pre-approved that
  environment and tool. Either way the preview, bound identifiers, and stripped-jar refusal apply
  ([Anypoint access](anypoint-readiness.md#consent-and-privacy)).
- **Confirm the result from the platform.** A deploy call can keep running after the client or
  session ends. Read `get_deployment_spec` before reporting success or failure.

## Watch

1. **Brief the watch first.** Before applying, share the start time in UTC, the new artifact, and
   the rollback target with everyone watching.
2. **Check at fixed points** measured from the apply minute: a few minutes after settling, then at
   increasing intervals through the first hour, after one full cycle of every scheduler, and again
   the next day. Choose the exact points from the app's traffic and schedules, and write them down.
3. **Timestamp every check.** A check that read stale data is not a green checkpoint.
4. **Confirm which artifact runs before reporting.** A report about a release that has since been
   replaced is wrong in every detail.
5. **Read both generations.** Logs are stored per deployment spec. Pass `previousSpecs` to the log
   tools. Lifecycle errors seconds after the old replicas stop are shutdown noise; the same errors
   after the new replicas start are not. A failed update leaves the desired version different from
   the last-successful one while the old version keeps serving.
6. **Test watch scripts on live data.** An unsupported shell comparison or a filter that never
   matches reports green without checking anything. Prove each check can fail.

## Healthy, defined positively

Absence of errors is not health. Call a release healthy only when every check that applies to the
app's actual sources holds; mark the rest not applicable rather than skipping them silently (an
HTTP-only API has no channels or watermarks):

- The desired and last-successful versions name the new artifact, and no replica restarts after
  settling.
- The start-up log shows the expected version, deployment mode, and object store.
- Every subscription channel is subscribed. A single transient subscribe failure that recovered is
  acceptable when the connector profile lists it.
- Only known-benign connector lines appear, and they still recur on their normal cadence.
- No new error class and no dependency-limit error appears.
- Watermarks advance, and at least one scheduled and one event-driven path complete end to end.
- The logs contain no session or bearer markers (`scan_logs_for_credentials` with `previousSpecs`, which returns counts only).
- The start gap is reconciled or accepted.
- Old-generation memory is within the app's baseline.

At low volume, zero errors proves little. For a fix to an intermittent fault, the pass condition is
the fault's own trigger passing, for example surviving the periodic reconnect that used to fail.

## Roll back or hold

- **Re-derive the rollback from the observed cause** before running it. A scripted step that writes a
  property back can reproduce the failure on the old artifact. Roll back without a property write
  unless the cause is a property.
- **Compare with the previous version before rolling back.** When the old and new versions fail the
  same way, the code change is unlikely to be the cause. Check shared changes the release made
  (platform properties, credentials, state the new version wrote) before deciding; when the cause is
  outside the release (a target system, credentials, the platform), a rollback only adds a start and
  its loss.
- **Roll back subscription apps with no overlap**: `rollback_app` with `mode: stopStart`.

## Hypercare

Run the period after a significant release as a freeze with exit criteria.

- **Freeze.** No deploys or property writes except a backout or a fix for a confirmed defect.
- **Watch on a cadence**, more often at first. Cover per-route failures against a pre-release
  baseline, dependency-limit errors, reconnects per channel, old-generation memory, and restarts.
  Classify every restart with the audit log; see
  [platform-initiated restarts](../../mule-troubleshooting/references/deployment-failure-triage.md#platform-initiated-restarts).
- **Reconcile events.** Compare records that reached the trigger state with completed side effects.
  Silence cannot show a lost event.
- **Exit on measured criteria only:** no unclassified server errors; every route seen or explained;
  per-route failures within a bound scaled to traffic and agreed with the service owner, for example
  `failures_now <= ceil(failures_before * calls_now / calls_before) + tolerance`, which applies only
  when the baseline had calls (a route with no baseline traffic is judged case by case); no
  unexplained restarts;
  the event gap reconciled or accepted; and business sign-off. When traffic is too thin to judge,
  extend hypercare rather than exit.

## Tag the release

Tag the commit the deployed artifact was built from, after production has run it through a quiet
period. A tag is the claim that this source is what production proved. A rolled-back release gets no
tag; a superseded build of the same version goes on the never-deploy list.
