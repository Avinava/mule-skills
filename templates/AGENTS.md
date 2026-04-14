# <!-- PROJECT_NAME --> — Project Guide

## What This Project Does

<!-- Describe what this project does in 2-3 sentences. Include:
- What type of API is it? (Process API, System API, Experience API)
- What systems does it integrate?
- Where does it run? (CloudHub 1.0, CloudHub 2.0, Runtime Fabric, On-Prem)
-->

This is a **MuleSoft Mule 4** <!-- PAPI/SAPI/XAPI --> that <!-- DESCRIPTION -->. It runs on <!-- DEPLOYMENT_TARGET --> and communicates with <!-- COMPANION_API --> for <!-- PURPOSE -->.

---

## Project Structure

```
src/main/mule/
├── global.xml                    # Global configs (HTTP, connectors)
├── interface.xml                 # API router (APIkit)
├── implementation/               # Business logic flows
│   └── <!-- LIST YOUR FLOW FILES -->
└── queues/
    └── <!-- LIST YOUR QUEUE/SCHEDULER FILES -->

src/main/resources/
├── properties/
│   ├── local.yaml / dev.yaml / prod.yaml           # Environment configs
│   └── secure/                                      # Encrypted credentials
└── dwl/                                             # DataWeave transform modules
    └── <!-- LIST YOUR DWL FILES -->
```

---

## Key Integration Flows

<!-- Add tables documenting your key flows. Example format: -->

### Entity Sync
| Entity | Direction | Trigger |
|--------|-----------|---------|
| <!-- Entity --> | <!-- Direction --> | <!-- Trigger type --> |

### Scheduled Jobs
| Flow | Trigger | Purpose |
|------|---------|---------|
| <!-- Flow name --> | <!-- Scheduler/Event --> | <!-- Description --> |

---

## Architecture Patterns

<!-- Document the architectural patterns used in this project. Common patterns include: -->

- **API Layering** — <!-- e.g., PAPI never calls external systems directly -->
- **VM Queues** — <!-- e.g., Schedulers publish to VM queues, listeners consume -->
- **Error Logging** — <!-- e.g., All errors flow through errorLogFlow -->
- **Secure Properties** — Production uses `${secure::property}` syntax with encrypted YAML files. Sandbox builds strip the `secure::` prefix.

## Content-Hash Dedup Architecture

<!-- If your project uses content-hash deduplication, document it here.
This is critical — when you add/remove fields from DWL transforms,
the corresponding hash must be updated. -->

> **⚠️ CRITICAL RULE:** When you add or remove a field from any DWL transform listed below, you MUST update the corresponding hash subflow to include/exclude that field. A stale hash will silently skip records that have genuinely changed.

### Hash Registry

| Flow | Cache Key | Hash Subflow | Hashed Fields | DWL Transform |
|------|-----------|-------------|---------------|---------------|
| <!-- Flow --> | <!-- Key pattern --> | <!-- Subflow name --> | <!-- Fields --> | <!-- DWL file --> |

---

## Configuration

Environment-specific settings are in `src/main/resources/properties/{env}.yaml`:

| Config Area | Key Properties |
|-------------|----------------|
| <!-- Area --> | <!-- property.key --> |

---

## Build & Deploy

```bash
# Build using MCP tool (recommended)
# The mule-build MCP server handles Maven packaging

# Or use shell scripts:
./build.sh sandbox       # Strips secure:: prefixes for dev
./build.sh production    # Keeps secure:: prefixes for prod
```

The app deploys to **<!-- DEPLOYMENT_TARGET -->** as `<!-- APP_NAME -->`.

---

## Known Tech Debt

<!-- Track tech debt items here. Use strikethrough for resolved items. -->

- <!-- **Item description** — details -->

### DataWeave Gotchas
- **Field names cannot start with `_`** — DWeave requires identifiers to start with a letter. Use `resolvedProject` not `_resolvedProject`. See the `mule-development` skill for full rules.
- **`try()` requires explicit import** — `import try from dw::Runtime` must be added when using the `try()` function.
- **Batch Jobs & Kryo Serialization** — Never use `output application/java` to create thick, nested payloads that persist across `<batch:step>` boundaries. This crashes the batch engine's Kryo serializer. Keep large payloads as `application/json` strings.
- **Scatter-gather replaces payload** — After scatter-gather, access results via `payload.'0'.payload`, `payload.'1'.payload`. Save original payload to a variable before scatter-gather if needed downstream.
- **Null-guard SOQL variables** — Always `!isEmpty()` check variables before embedding them in SOQL strings. A null variable produces `WHERE Id = 'null'` which returns 400 errors.
- **Include all downstream fields in SOQL** — If a DWL transform accesses `vars.contact.AccountId`, the SOQL query must `SELECT AccountId`. Missing fields cause silent `null` values.
- **`idleTimeout` must be ≥ `responseTimeout`** — If `idleTimeout` fires first, Grizzly kills the connection mid-request, causing silent HTTP failures.

---

## Documentation

<!-- Link to your project-specific docs -->

Detailed docs are in the [docs/](./docs/) folder:
- <!-- [Topic](./docs/topic.md) — Description -->
