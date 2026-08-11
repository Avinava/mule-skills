# Privacy and evidence

## Contents

1. [Evidence states](#evidence-states)
2. [Sensitive-data boundary](#sensitive-data-boundary)
3. [Safe configuration documentation](#safe-configuration-documentation)
4. [Examples and identity](#examples-and-identity)
5. [Pre-delivery review](#pre-delivery-review)

## Evidence states

Use these states when confidence affects interpretation:

| State       | Meaning                                                  | Treatment                                         |
| ----------- | -------------------------------------------------------- | ------------------------------------------------- |
| Verified    | Directly established by current source or configuration  | State as current behavior and cite the source     |
| Provided    | Business context supplied by the user or a stakeholder    | Attribute it; do not use it to prove runtime      |
| Inferred    | Strongly suggested by several facts but not explicit     | Label the inference and list supporting evidence  |
| Unresolved  | Conflicting or missing evidence                          | Put in `Open questions`; do not choose an answer  |
| Recommended | A proposed improvement, not current behavior             | Keep separate from current-state documentation    |

Prefer repository-relative evidence such as a flow name plus file path. Do not cite local absolute
paths. For diagrams, cite the principal source flows in the paragraph following the diagram.

Before publishing a design decision, distinguish:

- an explicit ADR or comment explaining intent
- a repeated implementation pattern that supports an inference
- a generic MuleSoft best practice that is not evidence of this project

Only the first is an established rationale. Label the second as inferred and keep the third in a
recommendation section if it is relevant.

User answers can establish intended purpose, audience, ownership, terminology, or expectations as
`Provided` context. They cannot establish that a flow, connector, retry, policy, or deployment
behavior exists. Cross-check those claims against implementation evidence and surface conflicts.

## Sensitive-data boundary

Never include:

- passwords, tokens, API keys, client secrets, signing material, or session identifiers
- private keys, certificates, keystore/truststore content, or encryption keys
- decrypted secure properties or committed ciphertext copied as an example
- real customer payloads, log bodies, record identifiers, or personal information
- private hostnames, tenant/account identifiers, usernames, or email addresses unless the user has
  explicitly asked for a private internal document and the value is necessary
- local filesystem paths or developer-machine configuration

Do not open binary credential files to decide whether they are safe. Inventory their required role
only when source configuration references them.

Treat files named like `.env`, `secure-*`, `secrets.*`, `*.jks`, `*.p12`, `*.pfx`, `*.key`, and
deployment secret stores as sensitive by default.

## Safe configuration documentation

List the property key, source, purpose, and evidence-backed requirement status. Replace values with
one of these forms:

```yaml
http:
  port: "${HTTP_PORT}"

target:
  host: "api.example.invalid"
  clientSecret: "<redacted>"
```

Use `${PROPERTY_KEY}` for runtime-provided values, `api.example.invalid` for a neutral hostname, and
`<redacted>` for secrets. Do not use realistic credentials, domains, record IDs, or organization
names in reusable examples.

Document authentication at the mechanism level, for example `OAuth 2.0 client credentials using
secure property references`. Do not reproduce the configured principal or credential material.

## Examples and identity

In documentation generated for a current project, preserve its real non-secret project and system
names unless the user requests anonymization. This makes internal documentation usable.

In this reusable skill and its references, use only neutral identities:

- `example-process-api`
- `example-system-api`
- `Calling Application`
- `Source System`
- `Target System`
- `api.example.invalid`

Never transplant a name, endpoint, field mapping, architecture image, sample payload, or design
detail from a different customer project. Learn the documentation pattern, then re-derive facts from
the current project.

Do not promote exact schedules, traffic volumes, retention windows, error counts, incident
timestamps, log messages, or tuning values from one project into reusable guidance. State the
general mechanism and require the current project's evidence to supply values.

When source examples look production-like, prefer schema-derived synthetic examples. If a copied
fragment is necessary, replace personal, customer, host, tenant, and record identifiers while
preserving only the structural behavior being explained.

## Pre-delivery review

Perform these checks over every changed document:

1. Search for credential-assignment patterns, private-key headers, bearer tokens, and ciphertext.
2. Search for local absolute paths, emails, private domains, tenant IDs, and record-like identifiers.
3. Confirm configuration tables contain keys and placeholders rather than values.
4. Confirm diagrams use safe labels and contain no environment-specific secret.
5. Confirm every important claim has a source and every inference is labeled.
6. Confirm recommendations are not written as current behavior.
7. Confirm sample payloads are synthetic and minimal.
8. Run `scripts/audit_documentation.py`; use `--denylist-file` when the project supplies terms that
   must not appear.
9. Confirm stakeholder-provided context is attributed and skipped questions did not become
   unsupported claims.

Treat an audit finding as a blocker until it is removed or explicitly reviewed as a safe false
positive.
