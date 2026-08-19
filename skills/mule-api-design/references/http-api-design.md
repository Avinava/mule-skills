# HTTP API design

Use HTTP semantics from RFC 9110. Conventions improve predictability, but consumer clarity and verified
organization rules outrank aesthetic uniformity.

## Resources and URIs

- Model durable domain resources and relationships with nouns. Prefer plural collection names when the
  domain naturally has collections.
- Keep path segments stable, readable, and consistently cased; lowercase kebab-case is a defensible
  default when no organization convention exists.
- Use opaque identifiers in path parameters. Do not encode mutable names, personal data, tenant details,
  or implementation technology into paths.
- Use nesting only when the parent is required to identify or authorize the child.
- Use action subresources only when the operation is not honestly create, retrieve, replace, patch, or
  delete. Name the domain transition, not an RPC implementation method.
- Put filtering, sorting, pagination, field selection, and search criteria in query parameters when they
  select or shape a collection representation.

Do not require a version prefix, trailing-slash policy, or `/api` segment merely because it is common.

## Methods

| Method | Use | Safety/idempotency expectations |
| --- | --- | --- |
| GET | Retrieve a representation | Safe and idempotent; no request body |
| HEAD | GET metadata without response content | Safe and idempotent; no request body |
| POST | Create under a collection or process a request | Not idempotent unless the contract defines a mechanism |
| PUT | Create or fully replace state at a known URI | Idempotent intent; define omitted-field behavior |
| PATCH | Apply a partial modification | Define patch media type, validation, and concurrency |
| DELETE | Remove or make a resource unavailable | Repetition should converge on the same resource state |
| OPTIONS | Advertise communication options when needed | Safe and idempotent |

Method idempotency describes intended effect, not identical status codes or response bodies on every retry.

## Responses

- Use `201 Created` with `Location` when a resource was created and its URI is known; use `202 Accepted`
  only with an observable async status mechanism; use `204 No Content` only when no representation helps.
- Use conditional requests (`ETag`, `If-Match`, `412`) when lost updates matter.
- Distinguish malformed requests, authentication, authorization, missing resources, state conflicts,
  unsupported media, validation, rate limits, and service failures when consumers act differently.
- Do not return a success status with an error envelope or use `500` for every failure.

Sources: [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110),
[RFC 3986](https://www.rfc-editor.org/rfc/rfc3986),
[RFC 5789](https://www.rfc-editor.org/rfc/rfc5789), and
[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111).
