# Deployment failure triage

## Contents

- [Triage order](#triage-order)
- [Pod and replica failure signals](#pod-and-replica-failure-signals)
- [Deployment failure cause checklist](#deployment-failure-cause-checklist)
- [Decoded common error messages](#decoded-common-error-messages)

Read this when a deployment does not reach a running state, a replica restarts repeatedly, or an
application starts and then fails. Treat every signal as a hypothesis starter. Confirm with source,
configuration, and aligned platform evidence, and verify wording against the installed runtime and
deployment target.

## Triage order

1. Establish the transition: which version and configuration were being deployed, to which target,
   and what state the platform reports now. Record the Anypoint access state when it limits scope.
2. Separate platform failures (schedule, pull, resource, readiness) from application failures
   (startup, configuration, dependency) before reading deeper.
3. Read deployment history and replica events, then startup logs for the failing replica, then the
   effective configuration. Stay read-only until a discriminating check points at a cause.
4. Compare with the last successful deployment: artifact, runtime and Java, connector set,
   properties, resource sizing, and environment inputs.
5. Do not restart, roll back, or redeploy as a diagnostic step unless the user asks for that action.

## Pod and replica failure signals

| Signal | What it suggests | Discriminating checks |
| --- | --- | --- |
| Replica never becomes ready; startup logs end early | Startup failure or a readiness probe that never passes | Last startup log line, listener binding, and whether dependent resources were reachable |
| Repeated restarts shortly after start | Crash loop from startup error or memory kill | Exit reason and the logs before each restart; compare restart spacing with startup time |
| Terminated with an out-of-memory reason at the container level | Process exceeded its memory allotment, which can differ from a JVM heap error | Compare container limit, heap settings, native memory, and payload or concurrency growth |
| JVM out-of-memory error in logs | Heap or another JVM region exhausted | Which region, old-generation trend, and the memory checklist in `signatures-and-pressure.md` |
| Stuck pending or never scheduled | Insufficient capacity or an unsatisfiable resource request | Requested sizing against what the target can place; platform events |
| Image or artifact fetch fails | Missing, unpublished, or inaccessible artifact | Whether the version exists in the repository, and access for the deploying identity |
| Healthy start, then failure on first traffic | Lazy initialization or dependency fault | First request path and the connection that fails |
| One replica unhealthy while others are fine | Replica-local state or placement | Compare replica logs and metrics before changing configuration |

An out-of-memory termination at the container level and an application error are different failures.
Confirm which one occurred before sizing anything, and never recommend resource values without
observed workload.

## Deployment failure cause checklist

Work through these as hypotheses, not a sequence of fixes.

- **Artifact:** the packaged version is the intended one, built for the target runtime, and
  published where the deployment reads it.
- **Runtime and Java:** the runtime version and Java level match the artifact's declared minimums and
  every connector's requirements. Use [`mule-dependencies`](../../mule-dependencies/SKILL.md) rather
  than memory for compatibility.
- **Properties:** every referenced property key exists in the target environment, secrets resolve,
  and the secure-properties key is supplied. Check key presence, never values. Check that each
  secret's placeholder matches its supply model (`${secure::key}` for the encrypted file, `${key}`
  for a platform secure property).
- **Dependencies at startup:** connectors that connect eagerly can fail the whole start when the
  target is unreachable. Check network path, certificates, and trust configuration.
- **Resources:** requested sizing, replica count, and any quota or entitlement of the target.
- **Ports and listeners:** the listener binding fits the platform's expected port and host
  configuration, and no two listeners conflict.
- **Duplicate or conflicting config:** duplicate configuration names, missing global elements, or a
  profile that differs between environments.
- **Version drift:** the running version, logged application version, and packaged artifact agree.
- **Rolling transition:** old and new replicas overlapping can show lifecycle errors and duplicate
  processing. Confirm with replica events, not timestamps alone. Logs are kept per deployment spec,
  so read the previous spec as well (`previousSpecs` on the log tools) before concluding that the
  old replicas logged nothing.
- **Permissions:** the deploying identity has the right in the target environment.

## Decoded common error messages

Messages vary by runtime and connector. Read each as the mechanism it names, then confirm.

| Message shape | Mechanism | Next check |
| --- | --- | --- |
| Application failed to start, with a root cause line below | A startup component failed; the first cause is the lead | Read the deepest cause, not the wrapper |
| Unresolved placeholder or property not found | A key is referenced but not supplied in this environment | Compare keys against the environment inputs |
| Secure property not found although it is set in Runtime Manager | Supply models mixed: a platform secure property referenced as `${secure::key}`, which reads only the encrypted file | Compare the placeholder with the key's model; see secret supply models in `mule-development` |
| Unknown or invalid connection element, or a connection parameter that is not allowed | The connection type does not exist in the installed connector version | Check connection types by version in `mule-connectors` and `mule_versions.py notes` |
| Could not resolve a dependency, or class not found | Packaging or connector set mismatch | Compare packaged dependencies with the declared set |
| Unsupported class version or unsupported Java level | Artifact or connector built for a newer Java than the runtime | Compare Java levels; see the compatibility checks above |
| Address already in use, or bind failure | Two listeners or a platform port mismatch | Inspect listener configuration |
| SSL handshake or certificate path error | Missing trust, expired or mismatched certificate, or a wrong protocol | Check trust configuration and the peer certificate chain without opening key material |
| Connection refused or unknown host at startup | Dependency unreachable from the target, or a wrong endpoint | Confirm network path and endpoint configuration |
| Authentication or authorization failure at startup | Credential absent, expired, or lacking rights | Check that the credential resolves and holds the needed rights, never its value |
| Out of memory during start | Initialization needs more than the allotment, or large eager loads | Distinguish heap from container limit; review eager loading |
| Deployment timeout or never reaches started | Slow startup versus a failing readiness check | Compare startup duration with the platform's wait and check readiness criteria |
| Artifact not found | Version missing from the source the deployment reads | Confirm publication and access |

Record each match as Hypothesis until a discriminating check, such as comparing with the last
successful deployment, separates it from the alternatives.
