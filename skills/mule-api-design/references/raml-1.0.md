# RAML 1.0

Use RAML 1.0 for new RAML work. Preserve RAML 0.8 only for verified compatibility.

- Start the root with `#%RAML 1.0`; fragments declare their exact fragment type.
- Define title, description, meaningful version/base URI, media types, security, types, and resources.
- Keep required/nullability/example semantics aligned in `types`.
- Use libraries for coherent reusable declarations, traits for cross-cutting operation facets, and resource
  types for genuinely repeated resource shapes; avoid abstractions that obscure the rendered contract.
- Keep `uses` aliases stable and include paths relative, local, and portable.
- Give operations stable `displayName` values when tools map them as operation identifiers.
- Describe every response and payload, and validate examples against types.

Verify which local file or published asset/version APIKit binds. A similar copy is not authoritative. Route
APIKit, implementation, consumer, and MUnit changes to sibling skills. Validate the complete multi-file
project; do not flatten it merely to hide include problems.

Sources: [RAML 1.0 specification](https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md)
and [APIKit compatibility](https://docs.mulesoft.com/apikit/latest/apikit-compatibility).
