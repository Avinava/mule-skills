# Data and errors

Representations are contracts, not serialized database rows.

- Use one field-naming convention per public API. `camelCase` is a reasonable JSON default when no
  verified organization convention exists.
- Define required/optional, absent/`null`, defaults, read-only/write-only, and unknown-property behavior.
- Treat identifiers as opaque strings unless arithmetic is part of their public meaning.
- Use RFC 3339 timestamps and distinguish instant, local date/time, and duration.
- Define money, decimal precision, unit, rounding, and large-integer encoding explicitly.
- Keep enums evolvable and tell consumers whether unknown future values are possible.
- Define arrays as ordered/unordered, bounded/paginated, and unique/non-unique where material.
- Declare every supported media type. Give schemas descriptions and schema-valid examples.

Use invented, neutral examples and reserved example domains; never paste a production payload or real ID.

## Error contract

Prefer RFC 9457 Problem Details when consumers and policy allow it. Otherwise use one consistent envelope
with a stable type/code, caller-safe title/detail, aligned HTTP status, safe correlation/instance reference,
field-level validation details, and truthful retry guidance.

Do not expose stack traces, connector messages, SQL, private hosts, tokens, internal IDs, or raw rejected
payloads. Separate caller-safe detail from internal observability.

Usually additive: new optional response fields/endpoints. Potentially breaking: removing/renaming fields,
changing type/meaning, requiring optional input, narrowing accepted values, or changing status/error behavior.
Enum additions can break closed-enum consumers.

Sources: [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457),
[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259), and
[RFC 3339](https://www.rfc-editor.org/rfc/rfc3339).
