# Artifact identity handoff

A build artifact and an authorized platform operation are separate outcomes. Use this protocol when
handing a packaged Mule application from `mule-build` to `mule-ops` and `anypoint-connect`.

## Record the local candidate

For a build result that exposes artifact identity, preserve the returned `jarPath` and
`artifact.groupId`, `artifact.artifactId`, `artifact.version`, and `artifact.sha256`. These describe
embedded Maven metadata and the exact packaged bytes. The display name, timestamped filename,
source POM, and intended version alone are not artifact identity. A version override must agree with
the embedded version, including when the build uses a staging copy and leaves the checkout unchanged.

Keep the validation ledger with the candidate: selected revision, build/test commands, lint execution
state and scope, tests skipped, and unresolved checks. A successfully packaged JAR is not evidence
that tests, full security review, or deployment verification succeeded. Never include deployment-info
machine/user fields, credentials, or secret-bearing configuration in a reusable report.

## Preview the platform destination

1. Establish authorized Anypoint access with
   `<skills-root>/mule-ops/references/anypoint-readiness.md`. A build handoff does not grant platform
   access or permission to publish or deploy.
2. Inspect the installed connector's tool schema before relying on new fields. Use `jarPath` for the
   exact candidate, and pass its SHA-256 as `expectedSha256` when supported. Do not silently drop a
   digest requirement when using an older release.
3. Start with the non-mutating preview (`confirm` omitted or false) for `publish_app_jar` or
   `deploy_jar`. Review the digest, Exchange group, asset ID, version, and the exact application and
   environment for deployment. An Exchange group can be the authorized organization rather than the
   embedded Maven group; state that mapping explicitly.
4. Default asset ID and version to embedded `artifactId` and `version` when supported. Preserve an
   explicitly approved coordinate remap using `assetId`, `assetVersion`, and `groupId`; disclose the
   source and destination identities rather than silently substituting a display name. Missing or
   ambiguous metadata requires an explicit mapping or a corrected package, not filename guessing.
5. Obtain approval for the exact publication and, separately or explicitly together, deployment.
   Preserve the connector's preview, confirmation, and authentication safeguards. For API-contract
   publication use its preview-token workflow; the JAR workflow does not replace that safeguard.

## Commit only the reviewed candidate

Carry the same `expectedSha256` into the approved mutation. If the bytes change after review, stop:
rebuild or re-inspect, preview again, and get approval for the changed candidate. A matching digest
protects byte identity; it does not prove safety, correctness, or authenticity.

Record returned publication coordinates as the deployment input, not an inferred filename. Publication
success is not deployment success: verify the requested runtime's actual version and status, and
report any pending transition or unverified runtime behavior. A local-source compatibility smoke
cannot authorize these operations or prove that a published pin implements them.

If an older installed release lacks identity or digest support, state the missing guarantee. Continue only
with a workflow whose required evidence and safeguards can be met; otherwise leave the handoff
unresolved. Do not repin to an unpublished package or claim a protected upload from an unguarded call.
