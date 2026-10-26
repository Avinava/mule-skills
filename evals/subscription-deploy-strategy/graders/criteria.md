---
type: llm
weight: 1
---

Pass only if the answer explains that a rolling update overlaps old and new replicas so events are processed twice, recommends stop-start or a recreate strategy for subscription apps, explains that ONLY_NEW without the connector's auto replay or resume option loses events published while the app is stopped or restarting, proposes enabling that option or another durable replay position within the retention window, and still requires idempotent consumers.
