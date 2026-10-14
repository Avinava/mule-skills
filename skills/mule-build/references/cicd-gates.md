# CI/CD gates

The order of gates for a Mule application pipeline. Read this when designing or reviewing a pipeline,
not for local one-off builds. Teams have their own CI product; this file fixes the sequence and the
decisions, not the syntax.

## Contents

- [Gate sequence](#gate-sequence)
- [Secrets in pipelines](#secrets-in-pipelines)
- [Promotion and rollback](#promotion-and-rollback)
- [Artifact immutability](#artifact-immutability)
- [CloudHub 2.0 versus Runtime Fabric inputs](#cloudhub-20-versus-runtime-fabric-inputs)
- [Verify against the installed version](#verify-against-the-installed-version)

## Gate sequence

Run gates cheapest and most deterministic first; stop at the first failure and report which gate failed.

1. **Format**: check, do not rewrite, in CI. Rewrites belong on a developer branch.
2. **Lint**: run mule-lint through the [standards protocol](../../mule-development/references/mule-lint-standards.md)
   and record execution state and scope. A skipped or partial lint is not a pass.
3. **Test**: run MUnit. Treat coverage as a map of what is untested, not as a quality score; a coverage
   threshold gate must never replace reading failing scenarios.
4. **Package**: build once, from the tested revision.
5. **Security scan**: dependency and secret scanning on the built artifact and its lockable inputs.
6. **Publish**: push the exact packaged bytes to the artifact repository.
7. **Deploy**: only the published artifact, to the first environment, then verify.

Record in the validation ledger which gates ran, which were skipped and why, per
[Artifact identity handoff](./artifact-handoff.md).

## Secrets in pipelines

- Inject secrets from the CI secret store at the step that needs them; never write them to the repository,
  the build log, the artifact, or a cache.
- Keep the property-encryption key out of the same place as the encrypted properties.
- Mask secrets in logs and fail the pipeline on echoed secret patterns.
- Use short-lived, least-privilege credentials per environment; rotation must not require a code change.
- Do not pass secrets as command-line arguments where process listings can expose them.

## Promotion and rollback

- Promote the same artifact through environments; only external configuration changes per environment.
- Keep a manual or policy approval before production, and make the approver see gate results.
- Define rollback before the first deploy: which previous artifact version is redeployed, how its
  configuration is restored, and how data or state changes are handled when the old version runs again.
- After deploy, verify the running version matches the published artifact, then check health and logs.

## Artifact immutability

A released version is never rebuilt or overwritten. A fix is a new version. Verify identity by checksum
and embedded metadata, not by file name or timestamp. Snapshot versions never reach shared
environments past development.

## CloudHub 2.0 versus Runtime Fabric inputs

Both need the artifact reference, the target, the runtime version, and per-environment properties and
secrets. They differ in target shape and sizing and scaling inputs (shared space or private space versus
a Runtime Fabric cluster and namespace). Do not reuse one target's deployment descriptor for the other;
read the platform's current deployment specification and preview before any mutation. Authorized
mutations follow `<skills-root>/mule-ops/references/anypoint-readiness.md`.

## Verify against the installed version

Confirm the Mule runtime, Java, Maven and plugin versions the pipeline image uses match the project
declaration. For the current connector, plugin and runtime versions, use
[mule-dependencies](../../mule-dependencies/SKILL.md) instead of pinning from memory.
