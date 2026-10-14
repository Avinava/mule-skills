---
type: llm
weight: 1
---

Pass only if the answer gives a concrete version taken from a named source (a live Exchange lookup, a version script, or a dated offline snapshot), states the minimum Mule version and Java requirement, and is honest about how it was verified (including saying so when the lookup could not run live). Fail if the version is asserted from memory with no source, taken from Maven Central, is a DEV or snapshot build, or is claimed as live-verified when it was not.
