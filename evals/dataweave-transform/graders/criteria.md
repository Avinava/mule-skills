---
type: llm
weight: 1
---

Pass only if the script declares output and media type, handles nulls explicitly, avoids nested searches in favour of grouping or indexing, and says something correct about streaming limits for large input. Fail on quadratic lookups or silent null coercion.
