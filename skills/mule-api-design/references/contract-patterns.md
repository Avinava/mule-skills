# Contract patterns

Apply only when the consumer task requires them.

- **Collections:** define maximum page size and stable ordering. Choose offset/page for bounded stable data;
  cursor pagination for changing or large data. Specify cursor opacity, filters, sort, counts, and links.
- **Idempotent POST:** define key scope, retention, request fingerprint, concurrent duplicates, and response
  replay. Reject key reuse with different input; a header alone is not a mechanism.
- **Concurrency:** use ETags/`If-Match` when lost updates matter. Define tag acquisition and `412`/`428`.
- **Long-running work:** `202` requires an observable job/status resource. Define states, polling/backoff,
  result/failure links, cancellation, retention, and duplicate submission.
- **PATCH:** select JSON Merge Patch, JSON Patch, or a typed domain patch; define absent/null, unknown paths,
  arrays, validation, and concurrency.
- **Bulk:** define atomic/per-item behavior, bounds, ordering, duplicate keys, partial failure, idempotency,
  and response correlation.
- **Versioning:** prefer compatible evolution. If breaking, choose URI/media/header/asset versioning from
  gateway and consumer constraints, then define support window, migration, and coexistence.
