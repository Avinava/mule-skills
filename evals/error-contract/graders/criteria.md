---
type: llm
weight: 1
---

Pass only if the answer uses one consistent error envelope (problem-details style) with a stable type and caller-safe detail, returns per-item outcomes or an explicit all-or-nothing policy instead of a 200 that hides failures, includes field-level validation details, echoes a correlation id, never leaks internals, and gives retry guidance (Retry-After) for temporary failures. Fail if bulk failures are hidden or internals are exposed.
