---
type: llm
weight: 1
---

Pass only if the answer streams or chunks the file instead of loading it whole, explains that streams are consumed once or need a repeatable strategy, bounds memory by concurrency and chunk size, handles per-record failures without losing the run, makes the load idempotent or restartable, and avoids invented numeric tuning values without workload evidence. Fail on whole-file in-memory designs or silent record loss.
