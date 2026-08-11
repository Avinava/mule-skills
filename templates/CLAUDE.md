# <!-- PROJECT_NAME --> — Claude Instructions

Read `AGENTS.md` for full project context. This file contains Claude-specific directives.

## Content-Hash Dedup — Mandatory Update Rule

<!-- If your project uses content-hash deduplication, include this section. -->

This project uses MD5 content hashing to deduplicate records in scheduler and listener flows. Hashes are computed from the fields consumed by downstream DWL transforms.

**When modifying any DWL file in `src/main/resources/dwl/`:**
1. Check the Hash Registry table in `AGENTS.md` → "Content-Hash Dedup Architecture"
2. If the DWL file is listed, find the corresponding hash subflow
3. If you added/removed/renamed a field in the DWL, update the hash subflow to match
4. A stale hash will silently skip genuinely changed records — this is a production-breaking bug

**Hash locations:**
<!-- Update these paths for your project -->
- Scheduler hashes: `src/main/mule/queues/schedulers.xml` (subflows at bottom)
- Entity hashes: <!-- path to hash subflows -->

## Build
Use the `/build` workflow or `mule-build` MCP tools. Do NOT call Maven directly.

## Documentation
Use the `document-mulesoft-project` skill to create or refresh project documentation.

## Salesforce Org
<!-- If your project connects to Salesforce, specify the org alias -->
The connected Salesforce org alias is `<!-- ORG_ALIAS -->`.
