---
type: llm
weight: 1
---

Pass only if the answer branches from the commit that built the running artifact, proven by comparing the deployed artifact with that commit, not from the default branch; versions the hotfix with a semantic prerelease qualifier such as 1.4.2-hotfix.1 and notes four-part versions are rejected; and requires diffing the hotfix artifact against the running one so only version metadata and intended files differ.
