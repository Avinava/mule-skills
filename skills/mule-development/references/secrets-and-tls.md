# Secrets, TLS, and credential handling

Use this reference when a change introduces or modifies credentials, secure properties, TLS
contexts, mutual TLS, or token based authentication to another system. It deepens the Security and
configuration gate in
[Invariant classes and cross-cutting gates](invariant-classes.md#cross-cutting-gates). Read the
Privacy and observability gate there as well, since secrets must never reach logs or fixtures.

## Contents

1. [Principles](#principles)
2. [Secure properties lifecycle](#secure-properties-lifecycle)
3. [Secret supply models](#secret-supply-models)
4. [Rotation](#rotation)
5. [External vault through a properties provider](#external-vault-through-a-properties-provider)
6. [TLS context and truststore hygiene](#tls-context-and-truststore-hygiene)
7. [Mutual TLS setup](#mutual-tls-setup)
8. [OAuth client credentials token cache and refresh](#oauth-client-credentials-token-cache-and-refresh)
9. [Review checklist](#review-checklist)
10. [Verify against installed runtime and connector versions](#verify-against-installed-runtime-and-connector-versions)

## Principles

- A secret has one owner, one source of truth, and a rotation path. If you cannot name all three,
  the design is incomplete.
- Secrets live outside the source tree and outside the artifact where the platform allows it.
  Configuration that differs by environment is injected per environment.
- Separate the key that protects secrets from the secrets it protects. Never store them together.
- Never print, log, or put a secret value in a fixture, a test, an error message, or a handoff
  document. Refer to the property name instead.
- Use least privilege: a credential grants only what the integration needs, per environment.

## Secure properties lifecycle

Secure properties encrypt values in a configuration file so the file can be stored and reviewed
without exposing the secrets.

| Stage | Decision |
|---|---|
| Creation | Encrypt with the project's chosen algorithm and mode; record which one in the handoff |
| Key supply | Provide the decryption key at deploy time through a secret channel, not in the repository |
| Storage | Commit only encrypted values; keep plaintext out of history, including past commits |
| Use | Reference by property placeholder; never copy a resolved value into another property or log line |
| Environment separation | Use a different key and different values per environment |
| Removal | Remove the property and its consumers together, then rotate if it was ever exposed |

- If plaintext ever reached version control, treat the secret as compromised and rotate it;
  deleting the commit does not undo the exposure.
- A key held in the same repository, image, or file as the encrypted values gives no protection.
- Fail fast at startup when a required secure property cannot be decrypted, with a message that
  names the property but not its value.

## Secret supply models

A secret reaches a Mule app through one of two models. The placeholder must match the model, and a
mismatch fails at deployment or startup with an unresolved property, not with a clear message.

| Model | Where the value lives | Reference in XML | Declared in |
|---|---|---|---|
| A. Encrypted file | `![...]` value in a properties or YAML file read by `secure-properties:config`; the key arrives at deploy time | `${secure::key}` | The `secure-properties:config` element and its file |
| B. Platform secure property | A Runtime Manager secure or protected application property, set per environment | `${key}` | `mule-artifact.json` `secureProperties` (masks on CloudHub 1.0; declare it anyway for portability) |

- `secure::` is required for, and resolved by, the Secure Configuration Properties module from its
  encrypted file ([secure configuration properties](https://docs.mulesoft.com/mule-runtime/latest/secure-configuration-properties)).
  A Runtime Manager property is supplied to the app as a plain property and read as `${key}`. The
  documentation does not say what `${secure::key}` does for a key that exists only in Runtime
  Manager; in practice the deployment failed. Treat the mix as a defect, not a style choice.
- Pick one model per key, record it in the handoff, and keep the placeholder, the declaration and
  the deployment input consistent. Both models can coexist in one app for different keys; the
  documented way to combine them is to supply the module's decryption key as a platform secure
  property. When a
  module-backed key is also listed in `secureProperties`, list it with its `secure::` prefix.
- Masking differs by target, so verify on the installed target before relying on it:
  - CloudHub 1.0: list keys in `mule-artifact.json` `secureProperties` and set values on the
    Runtime Manager properties tab
    ([CloudHub secure properties](https://docs.mulesoft.com/cloudhub/secure-application-properties)).
  - CloudHub 2.0: masking through `mule-artifact.json` or a file does not take effect; protect the
    property in Runtime Manager. Runtime Manager values override bundled ones
    ([CloudHub 2.0 properties](https://docs.mulesoft.com/cloudhub-2/ch2-manage-props)).
  - Runtime Fabric: protected properties reach the app unencrypted as custom properties and take
    precedence ([Runtime Fabric](https://docs.mulesoft.com/runtime-fabric/latest/manage-secure-properties)).
  - Hybrid servers: confirm who can read Runtime Manager values before choosing model B; model A
    keeps the value encrypted at rest.
- Static checks follow the same split. mule-build 3.1 or later reads `secureProperties`: a
  declared key referenced as `${key}` passes, a declared key referenced with `secure::` that no
  scanned file defines encrypted is an error (MB-SEC-006). `secure::` with no
  `secure-properties:config`, or with a config but no scanned file defining the key, is always a
  warning (MB-SEC-007): MuleSoft does not document how `secure::` resolves without the module, and
  a shared domain may provide one. On CloudHub
  2.0 and Runtime Fabric a protected key need not be declared, but declare it anyway so the checks
  and other targets agree, or record a reviewed `security.allow` exception in `mule-build.yaml`. See
  [the mule-lint standards protocol](mule-lint-standards.md) for the lint rule that still assumes
  model A. Never change a model B reference to `secure::` to satisfy a check.
- A plaintext Runtime Manager property whose name looks secret is a finding: move it to a secure or
  protected property and rotate it if it was readable.

### Supplying values without echoing them

Never pass a secret value as a command argument, in a tool call or in chat, because all three are
recorded. Resolve it on the machine that sends it:

- anypoint-connect 0.16 or later: the settings change takes secret sources (a project `.env`,
  `.properties` or flat JSON file, or environment variables) and resolves them on the server, and it
  can move an existing plaintext property to secure without reading it back.
- Without that tool: build the request body from the escrowed file with `jq` and send it on stdin,
  for example `jq -n --rawfile v <file> '{...}' | curl --data @- ...`, so the value never appears in
  `argv`, shell history or the transcript. Keep the escrow file outside the repository with owner-only
  permissions.

## Rotation

Rotation is a procedure, not an event. Design for it before the first deployment.

1. Inventory what uses the secret (flows, connectors, other systems, scheduled jobs).
2. Prefer a window where old and new credentials are both valid, so rollout order does not cause
   an outage. If the target cannot support overlap, plan a coordinated cutover.
3. Update the source of truth, then deploy consumers; restart or reload so the new value is read.
4. Verify with a harmless authenticated call, then revoke the old credential.
5. Record the date and owner; define a rotation cadence and an emergency path for exposure.

Cached tokens and connection pools can hold the old credential after the source changes. Include
their invalidation in the procedure.

## External vault through a properties provider

When the platform or organization uses an external secret manager, resolve secrets at startup
through a properties provider instead of embedding them.

- Choose the provider by what the deployment target supports and by the organization's standard;
  do not assume one is available.
- Authenticate the application to the vault with a workload identity or a short lived credential,
  not with a long lived secret stored beside the application. The vault credential is itself a
  secret and needs the same lifecycle.
- Decide the failure behavior: if the vault is unreachable at startup, fail fast; at runtime,
  decide whether cached values are acceptable and for how long.
- Scope each application to the paths it needs. Avoid one broad credential shared by every
  application.
- Keep an auditable record of who and what can read each secret, and make rotation in the vault
  reach the application (restart, reload, or refresh) by design.

## TLS context and truststore hygiene

A TLS context defines what the application trusts and what it presents.

- Trust the narrowest set of authorities that works: a dedicated truststore containing only the
  required issuers, not a broad copy of every public authority unless the integration truly
  needs it.
- Never disable certificate or hostname validation to make a connection work, including in
  non-production environments that share configuration with production.
- Pin protocol and cipher expectations to the organization's security policy; take the allowed set
  from that policy and the installed runtime, not from another project.
- Keep keystore and truststore files and their passwords out of the source tree; supply them per
  environment through the secret channel.
- Track certificate expiry as an operational item: record the owner, the expiry, and the renewal
  procedure. An expired certificate is an outage with a known date.
- When an issuer or intermediate changes, update the truststore before the change takes effect.
- Use separate contexts for separate trust relationships, rather than one context that trusts
  everything every connector needs.
- Diagnose handshake failures from the error detail (unknown issuer, hostname mismatch, expired,
  protocol mismatch) instead of loosening validation.

## Mutual TLS setup

Mutual TLS adds a client certificate that the server verifies.

1. Decide who issues the client certificate, who holds the private key, and how it is renewed.
2. Configure a keystore with the client key pair and a truststore with the server's issuer.
3. Load both into the TLS context for the specific connector or listener, not globally.
4. On the server side, define which client identities are accepted (issuer, subject, or a mapping)
   and how revocation or removal is handled.
5. Test the failure paths: no client certificate, an untrusted one, an expired one, and a valid
   one for the wrong identity. Each must fail closed with a clear, non-leaking error.
6. Include certificate renewal and the key's storage in the rotation procedure above.

Treat the client private key as a high value secret: restrict who can read it, never export it
into logs or support bundles, and rotate it on exposure or personnel change.

## OAuth client credentials token cache and refresh

For machine to machine calls using a client credentials grant, tokens are short lived and the
token endpoint is a shared, rate limited dependency.

- Cache the token per client identity and scope, with an expiry taken from the response. Do not
  request a new token for every call.
- Refresh proactively a short margin before expiry, and also on an authorization failure from the
  target, retrying the original call at most once with a fresh token.
- Make refresh safe under concurrency: one in-flight refresh at a time, with other callers waiting
  for it, so a burst does not stampede the token endpoint.
- Store the cache in a place whose lifetime matches the token and whose scope matches the
  application. A cache shared across replicas needs a clear owner and expiry; per replica caches
  are simpler and independent. Choose deliberately. See Class E for state rules.
- Never log the token or the client secret; log the client identity, scope, and expiry outcome.
- Handle token endpoint failure as a classified dependency failure (Class D): retry transient
  errors with limits, and fail fast on invalid client or credentials, which retrying cannot fix.
- Treat the client secret like any other secret: own it, rotate it, and invalidate the cache when
  it changes.

## Review checklist

- Every secret has an owner, a source of truth, and a rotation procedure.
- Every secret key uses one supply model, and its placeholder and declaration match that model.
- No secret-looking key is stored as a plaintext platform property.
- No secret value appears in source, history, fixtures, logs, errors, or handoff text.
- Decryption keys and encrypted values are stored and delivered separately.
- Certificate and hostname validation are enabled in every environment.
- Truststores are narrow; expiry dates have owners.
- Failure paths for mTLS and token acquisition were tested.
- Token caching and refresh are bounded, concurrency safe, and invalidated on rotation.

## Verify against installed runtime and connector versions

Property provider options, supported TLS settings, and token handling vary by runtime, connector,
and security module version. Before relying on a setting:

1. Read the runtime, connector, and security module versions from the project. If a newer or
   compatible release is in question, use [the mule-dependencies skill](../../mule-dependencies/SKILL.md)
   for version and compatibility lookups.
2. Check the installed version's reference for the secure property algorithms, provider options,
   TLS context attributes, and token handling operations.
3. Confirm the behavior against a non-production environment with representative failures: wrong
   key, expired certificate, rejected token.
4. Record any difference from this guidance in the handoff, and follow the installed version.
