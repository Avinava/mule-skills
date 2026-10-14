# Error contract

Design the error surface once, then implement it in one place. Read this when an API has more than a
couple of failure modes, accepts bulk input, or when handlers in different flows return different shapes.

## Contents

- [Envelope](#envelope)
- [One shared status mapping](#one-shared-status-mapping)
- [Validation errors](#validation-errors)
- [Bulk and partial success](#bulk-and-partial-success)
- [Correlation and caller safety](#correlation-and-caller-safety)
- [Retry guidance](#retry-guidance)
- [Verify against the installed version](#verify-against-the-installed-version)

## Envelope

Use a Problem Details body (`application/problem+json`) unless a verified organization convention or
gateway policy requires another shape. Whatever the shape, every error response carries the same members:

| Member | Rule |
|---|---|
| `type` | Stable, documented identifier per failure class. A URI reference or a short code; never free text. |
| `title` | Short, caller-safe, constant for a given `type`. |
| `status` | Equal to the HTTP status actually sent. |
| `detail` | Caller-safe explanation of this occurrence. Never copied from a connector message. |
| `instance` | Safe reference for this occurrence, usually derived from the correlation id. |
| extensions | Additive members such as `errors` (field details) or `retryAfter`. Consumers must ignore unknown members. |

Declare the envelope once as a reusable schema or data type in the contract and reference it from every
non-2xx response. Do not redefine it per resource.

## One shared status mapping

Keep a single table that maps internal error types to a public `type`, `title` and HTTP status, and
implement it in one shared error-handler module or global handler. Flows raise or propagate typed errors;
they do not build response bodies.

Decide the mapping by failure class, not by connector:

| Failure class | Status family | Notes |
|---|---|---|
| Malformed or schema-invalid request | 400 | Include field details. |
| Missing or invalid credentials | 401 | No hint about which part failed. |
| Authenticated but not permitted | 403 | |
| Unknown resource | 404 | |
| Method or media type not supported | 405 / 406 / 415 | |
| State conflict or failed precondition | 409 / 412 | Idempotency and concurrency collisions. |
| Well-formed but semantically rejected | 422 | Business rule violations. |
| Throttled | 429 | Retry guidance required. |
| Unhandled internal failure | 500 | Generic `detail`; internals go to logs only. |
| Dependency refused, down or unreachable | 502 / 503 | |
| Dependency too slow | 504 | |

Use a catch-all last, so an unmapped error type still yields the envelope with a generic 500 rather than
a platform default body. Add a test that fails when a new error type has no mapping entry.

## Validation errors

Return every field problem found in one response, not the first one. Each entry names the location
(JSON Pointer or parameter name), a stable reason code, and a caller-safe message. Do not echo rejected
values for sensitive fields, and never echo a raw payload.

## Bulk and partial success

For endpoints that accept many items, decide the policy in the contract before building:

- All-or-nothing: one failure rejects the request with the normal error status. Say so in the contract.
- Per-item outcomes: return a multi-status style response (207 or an agreed equivalent) with one result
  per input item, keyed by a caller-supplied item identifier, each result either a success or an envelope.
- Asynchronous: accept with 202 and a status resource; per-item failures live on the status resource.

Never return a plain 200 that hides item failures, and never return 207 when every item has the same
outcome. Define whether a retry of the whole request is safe (idempotency key or per-item natural key).

## Correlation and caller safety

- Accept an inbound correlation id, generate one if absent, and echo it in a response header and in
  `instance`. Use the same value in logs so support can find the occurrence.
- Do not expose stack traces, `error.description`, `error.detailedDescription`, connector messages,
  SQL, hostnames, tokens, internal ids or raw rejected payloads. Log them internally, with sensitive
  fields masked.
- Keep `title` and `type` stable across releases; changing them is a breaking change for consumers that
  branch on them.

## Retry guidance

State in the contract which statuses are safe to retry. For throttling and temporary unavailability send
a `Retry-After` header and mirror it in the body only if consumers need it there. Do not advertise
retry for 4xx validation or authorization failures. For non-idempotent operations, say that retry is
safe only with the documented idempotency key.

## Verify against the installed version

Check how the installed APIKit, HTTP connector and gateway policies emit their own error bodies and
statuses (router validation, listener failures, policy rejections). Make the shared handler normalize
them to this envelope, and confirm the policy-generated responses match it, or document the exception.
For library and connector versions, use [mule-dependencies](../../mule-dependencies/SKILL.md).

Sources: [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) and
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110).
