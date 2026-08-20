# OpenAPI 3.0

Use an OpenAPI 3.0.x version supported by project tooling. Do not use OAS 3.1 for APIKit unless current
compatibility documentation changes.

- Define `openapi`, complete `info`, explicit `servers`, and consumer-facing `paths`.
- Give every operation a stable unique `operationId`, description, security, parameters, allowed request
  body, and described responses.
- Declare every path parameter with `in: path`, `required: true`, and matching spelling.
- Put genuine reusable schemas, parameters, responses, examples, bodies, and security under `components`.
- Model payload media types under `content`; validate examples against schemas.
- Keep discriminator, null/absence, composition, and additional-properties semantics explicit.
- Treat server URLs/variables as public contract data; use neutral placeholders in reusable examples.

For OAS 2.0 maintenance, preserve `swagger: "2.0"`, definitions/parameters/responses layout, and its body
parameter/content-type model. Do not mix OAS 3 keywords into 2.0.

Sources: [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3) and
[APIKit compatibility](https://docs.mulesoft.com/apikit/latest/apikit-compatibility).
