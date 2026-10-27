# Release lessons

These lessons come from production releases, hotfixes, rollbacks and a hypercare period of Mule 4
applications on CloudHub 2.0. Those applications used Salesforce streaming listeners, scheduled
pollers and two replicas. Each lesson gives the symptom, its cause and the rule we follow now.
Numbers are what we observed; set your own thresholds from your app's baseline.

1. **Record what is running before you release.** `get_deployment_spec` returns the artifact
   reference, runtime patch version, replicas, update strategy, and the desired and last-successful
   versions. That artifact, recorded by full name and SHA-256, is your first rollback target. With
   the runtime version on record, a later silent platform patch shows up.
2. **Start a hotfix from the source of the running artifact.** In our case, production ran a build
   with no tag. Find the commit that built it, prove it by comparing the artifacts, and branch from
   that commit, not from the default branch.
3. **Platform properties override the packaged files.** In production, a Runtime Manager property
   silently replaced the value in the repository's properties file. Before reasoning from the
   repository, read the effective values with `get_app_settings`. A stale property keeps
   overriding until it is removed (`update_app` `removeProperties`) or the code stops reading
   that key.
4. **Diff every property the candidate reads against what production supplies.** Check the
   packaged files, the encrypted secure file and the platform properties. In our case, a branch
   that added new keys and changed `${secure::key}` to `${key}` passed every lower environment, but
   it would have failed to start in production.
5. **Never deploy a "stripped" build to production.** A build that rewrites `${secure::key}` to
   `${key}` (a sandbox or local-run build, or `strip_secure`) fails at start with a missing value
   for the secret key. Build production through the production build path.
6. **Diff the hotfix artifact against the running one.** Only the version metadata and the files
   you meant to change should differ.
7. **Take selector values from production data, not defaults.** In our case, a new sweep filtered
   on a status picklist's default value, while production writes a different status. It would have
   matched nothing; only a sandbox test against real data caught it. Query recent production
   records and run the exact query before release.
8. **A configuration value in the jar is not a tested behavior.** A release lowered a connector's
   HTTP pool to stay under a backend's concurrency limit. A paged search holds pool connections
   across its page calls, so it failed with `Max connections exceeded`, and we rolled back. A
   connection pool is not a concurrency limit, so cap concurrency where the work starts. Never
   shrink a pool without a test of the worst case.
9. **Keep the logged application version equal to the build version.** One release logged a
   version months old, so before-and-after comparisons were wrong. Use semantic versions with a
   qualifier for hotfixes (`2.3.0-hotfix.1`); the Mule Maven plugin rejects `2.3.0.1`.
10. **Make MUnit boot before trusting it.** In our case, the committed toolchain never booted:
    `munit-runner` and `munit-tools` were hardcoded to an old MUnit 2.x release while the plugin
    property moved. The run failed with the MUnit extension refusing Java 17, and zero tests ran.
    - Use one MUnit version for the plugin, runner and tools. MUnit supports Java 17 from 3.1.0.
    - Run `check_compatibility`, but note that it reads the plugin version, not the two test
      dependencies.
    - When production's runtime cannot run the tests, commit a test-only Maven profile. It sets the
      MUnit version, a test runtime, a JDK enforcer rule, and placeholders for secure keys.
    - Prove the profile leaves the packaged artifact unchanged.
    - `run_tests` uses the MCP server's JDK.
11. **If tests cannot run, say so.** Name the substitute evidence, such as DataWeave fixture tests
    or a harness that runs the changed flow against a stub. One such harness found a real bug.
    Never call the change tested.
12. **Build fixtures from real production shapes.** Three successive "fixes" passed tests and failed
    in production. The fixture held a value that production sends as an empty key.
13. **Write the rollback plan before the release.** Name the target artifact by full name and
    digest, and say whether rolling back needs a property write (prefer targets that need none).
    Keep a never-deploy list: superseded builds of the same version, withdrawn assets, and targets
    that predate a property or credential the environment now requires.
14. **Re-derive the rollback from the observed cause before running it.** A scripted rollback step
    that wrote a property back would have reproduced the failure on the old artifact. Roll back
    with no property write unless the cause is a property.
15. **When old and new versions fail the same way, do not roll back.** One example: a Salesforce
    org issued client-credentials tokens and refused each on first use (`INVALID_SESSION_ID`) for
    about 20 minutes. The previous integration failed identically, so the cause was outside the
    release. A rollback would only have added a restart.
16. **Map session and login refusals to a retryable status.** The integration answered 400 for
    `INVALID_SESSION_ID`, so consumers wrote records off as permanently failed although Salesforce
    had done nothing. Answer 503, make re-login single-flight with a cooldown, and write records
    off only on a permanent status.
17. **A `<try>` around an outbound call can disable its retry budget.** Swallowing the error
    skipped the retries and marked the record failed after the target may have committed it. Send an
    external id on creates, look the record up after an ambiguous failure, and reuse it if it
    exists.
18. **Every start loses something.** That covers a deploy, a property write, a restart, a scale, a
    rollback, a platform patch and a replica the platform replaces. Write down the accepted loss
    before each one:
    - In-memory replay positions and in-flight `until-successful` retries are lost.
    - Persistent VM queue messages stay with the replica that is replaced.
    - Object Store entries and polling watermarks survive only on a persistent, platform-managed
      store.
19. **Prove store persistence from the logs, not from the store listing.** One environment kept
    its watermarks and another lost them and replayed hours of backlog. The platform's store
    listing was empty for both. The start-up log names the store (`Using Cloud Object Store`). The
    first poll logs a start from the stored position, not that no watermark is present.
20. **Where positions are not durable, pin the listener start in the same change.** Set the
    polling start value to "now minus a margin" in the same update as the redeploy.
21. **A property write is a full redeploy.** A "one-line" flag change took about four minutes,
    with two replicas overlapping, and on non-production it set off a replay burst. Treat every
    property write as a release, and put the artifact and all its properties in one `update_app`.
22. **Never roll out subscription apps with a rolling update.** During the overlap, both replica
    generations subscribe to every streaming channel and poll every source, so events are
    processed twice. Their combined calls also hit the backend's concurrency limit. Use
    `mode: stopStart` (on `update_app` and `rollback_app`) or the recreate strategy.
23. **A "new events only" Salesforce listener loses events at every app start.** Within a running
    app it resumes each channel after the periodic `403::Unknown client` reconnect from the last
    replay id received. Across a start, each channel begins at the newest event. The id also
    advances on receipt, so work queued in memory is lost at a restart. Reconcile the start gap
    after every start, or enable the connector's auto replay with idempotent consumers.
24. **A connected channel can go silent.** One channel stopped delivering, then delivered its
    backlog at the next re-handshake, up to half an hour late. Our success logs said 100%, because
    the events were delayed, not failed. A connector upgrade did not stop it. Measure delay per
    record (created to processed) and keep a reconciliation sweep for business-critical events.
25. **An event can arrive before its record is readable.** It arrived about 70 ms after creation, a
    lookup found nothing, and a guard skipped a valid record. Retry a not-found lookup briefly,
    treat a failed lookup as an error, and make every skip visible.
26. **Check the publishing trigger before calling an event lost.** Each event or topic publishes
    only on its own condition. A quiet listener is not a stalled one.
27. **Never raise a connector's streaming package to DEBUG in production.** A diagnostic hotfix
    did, and the Salesforce streaming transport wrote session ids and authorization headers to the
    log. We rolled back within five minutes and revoked the session; the lines stay readable for
    the log retention. After any logging change, search the new logs for session and bearer markers
    before calling the deploy healthy.
28. **Restarts can come from the platform.** An app restarted at a time when nobody deployed. The
    audit log (`get_audit_log`, filtered to `Application` and the mutating actions) showed
    `Modify` by user `Anypoint Staff` with client `appmgr_autopatcher`. Every app was modified in
    the same window, the artifact and properties were unchanged, and the runtime patch version
    moved: a platform runtime patch. Other platform signatures: `Replica Restarted` by
    `Anypoint Staff` means a replica was restarted or moved. `Patch Fabric` and `Patch Network`
    entries mean infrastructure maintenance. A team member or pipeline identity, with a changed
    artifact or properties, means your own change. Filter the query, because an unfiltered
    multi-day audit log overflows the response.
29. **A platform patch is still a start.** Run the post-start checks anyway: reconcile the listener
    gap, re-read the scheduler times, confirm the runtime version.
30. **Fixed-frequency schedulers re-anchor at every start.** Run times moved after each deploy and
    after the platform patch, so watches keyed to clock times misfired. Watch in time windows, and
    use cron when wall-clock timing matters.
31. **Read both replica generations' logs.** Logs are stored per deployment spec, so pass
    `previousSpecs` to the log tools. A burst of "is stopped" lifecycle errors seconds after the
    old replicas shut down is shutdown noise; the same errors after the new replicas start are not.
    A failed update leaves the desired version different from the last-successful one while the
    old version keeps serving.
32. **Watch every release at fixed checkpoints.** Check at +5, +15, +30 and +60 minutes from the
    apply minute, then after a full cycle of every scheduler, then at 2 hours and 24 hours. Before
    starting, send watchers the start time in UTC, the artifact and the rollback target. Timestamp
    every poll, because a stale poll is not a green checkpoint. Confirm which artifact runs before
    reporting: one watch report described a release that had been replaced hours earlier.
33. **Define "healthy" positively.** A release is healthy when all of these hold:
    - The desired and last-successful versions name the new artifact, and no replica restarts
      after settling.
    - The start-up log shows the expected version, mode and store.
    - Every channel is subscribed. One transient `503::Server is too busy` on subscribe that
      recovered is acceptable.
    - Only known-benign connector lines appear, and they are still recurring.
    - There is no new error class and no dependency-limit error.
    - Watermarks advance, and one scheduled and one event-driven path complete end to end.
    - The logs contain no credentials.
    - The start gap is reconciled.
    - Old-generation memory is within baseline.

    At low volume, no errors is not evidence. For a fix to an intermittent fault, the pass condition
    is the fault's own trigger passing, for example surviving two periodic reconnects.
34. **Test watch scripts on live data.** A shell comparison the shell did not support, and a host
    filter that never matched, both reported green without checking anything.
35. **Alert on ratios and on silence.**
    - A count rule ("5 failures per 15 minutes") paged a total outage 15 minutes late at low volume.
      Evaluate every few minutes on a minimum count plus a failure ratio.
    - Add a "no successful call for N minutes" rule, with N above the longest natural gap.
    - Don't page on benign ERROR lines such as the periodic streaming reconnect. Alert on their rate
      or on a missing recovery.
    - Memory alerts set near the GC sawtooth flapped every hour. Alert on sustained old-generation
      use, and check whether the threshold field is a fraction.
    - Tag probes so they neither page nor skew the counts.
36. **Gate the mutating Anypoint tools for agents.** `update_app_settings`, `update_app`,
    `restart_app`, `rollback_app` and `deploy_app` change production, and a property write is a
    redeploy. Keep them behind an approval in the agent's settings. A deploy call that outlives the
    client can continue in the background after the session ends, so confirm the result with
    `get_deployment_spec`.
37. **Run hypercare as a freeze with exit criteria.**
    - Allow no deploys or property writes except a backout or a confirmed-defect fix.
    - Watch twice a day at first, then daily. Cover per-route failures against a pre-release
      baseline, limit errors, reconnect counts per channel, old-generation memory, and unexplained
      restarts (classified with the audit log).
    - Reconcile events: records that reached the trigger state against side effects completed.
      Silence cannot show a lost event.
    - Exit only on measured criteria: zero unclassified server errors, every route seen or
      explained, and per-route failures within a traffic-scaled bound such as
      `failures_now <= ceil(failures_before * calls_now / calls_before) + 1`. Also require no
      unexplained restarts, the event gap reconciled or accepted, and business sign-off.
    - When traffic is too thin to judge, extend hypercare.
38. **Tag after production proves the release.** Tag the commit the deployed artifact was built
    from, after a quiet period in production. A rolled-back release gets no tag.
