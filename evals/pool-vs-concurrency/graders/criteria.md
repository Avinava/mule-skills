---
type: llm
weight: 1
---

Pass only if the answer explains that a connection pool is not a concurrency limit, that paged or streaming operations can hold connections across calls and fail with max connections exceeded, recommends capping concurrency where work starts (source, batch, parallel scopes, replicas), requires a worst-case test before shrinking a pool, and does not prescribe numeric values without workload evidence.
