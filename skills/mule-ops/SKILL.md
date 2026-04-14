---
name: mule-ops
description: Comprehensive cross-system analysis of Process API and System API Production logs, metrics, errors, and performance. Use this skill whenever asked to analyze logs, investigate errors, check performance, or do a health check.
---

# Production Log Analysis Skill

This skill provides a structured workflow for analyzing a **Process API (PAPI)** and its companion **System API (SAPI)** in Production. It covers logs, errors, metrics, memory, performance, and deployment activity — producing a single connected report.

## Configuration

> **Before using this skill, configure these values for your project:**
>
> | Variable | Value | Description |
> |----------|-------|-------------|
> | `PAPI_APP` | `<YOUR_PAPI_APP>` | Process API application name as deployed in CloudHub |
> | `SAPI_APP` | `<YOUR_SAPI_APP>` | System API application name as deployed in CloudHub |
> | `ENV` | `Production` | Default environment for analysis |

Replace `<YOUR_PAPI_APP>` and `<YOUR_SAPI_APP>` throughout this document with your actual application names.

## When to Use

- User asks to "check logs", "analyze errors", "what's going on in prod", "health check"
- Investigating a specific incident or error spike
- Routine daily/weekly health review
- Performance baselining or degradation investigation

## Prerequisites

- Anypoint Connect MCP server must be available
- Both apps are deployed in the target environment

---

## Step 1: Parallel Data Collection (PAPI + SAPI)

> **CRITICAL**: Make ALL of these calls in parallel to minimize latency. Use `hoursBack` matching the user's request (default: 24).

### 1a. Log Health (both apps, parallel)

```
mcp_anypoint-connect_get_log_stats(appName: "<YOUR_PAPI_APP>", environment: "<ENV>", hoursBack: <N>)
mcp_anypoint-connect_get_log_stats(appName: "<YOUR_SAPI_APP>", environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Total entries, unique transactions
- Level distribution (INFO/WARN/ERROR counts and %)
- Error rate
- Error spike windows (time + rate)
- Log retention range (SAPI may have shorter retention due to high volume + DEBUG noise)

### 1b. Error Analysis (both apps, parallel)

```
mcp_anypoint-connect_analyze_errors(appName: "<YOUR_PAPI_APP>", environment: "<ENV>", hoursBack: <N>)
mcp_anypoint-connect_analyze_errors(appName: "<YOUR_SAPI_APP>", environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Error groups: pattern, count, time range, affected flows
- Full context: before/after log lines for each error sample
- Correlation IDs for cross-system tracing
- Error types (HTTP:INTERNAL_SERVER_ERROR, CUSTOMER:NOT_FOUND, etc.)

### 1c. Log Patterns (both apps, parallel)

```
mcp_anypoint-connect_get_log_patterns(appName: "<YOUR_PAPI_APP>", environment: "<ENV>", hoursBack: <N>)
mcp_anypoint-connect_get_log_patterns(appName: "<YOUR_SAPI_APP>", environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Top patterns and % of log volume
- Active flows and their frequency
- Filtered/skipped record patterns
- Scheduler start/end pairs (confirm jobs complete)

### 1d. Performance Metrics (both apps, parallel)

```
mcp_anypoint-connect_get_metrics(environment: "<ENV>", hoursBack: <N>)
mcp_anypoint-connect_get_performance_metrics(environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Per-app: request count, avg response time, p50/p95/p99 latency
- Outbound request counts and response times
- Identify apps with high p99 or unusual request volume

### 1e. Memory & JVM Metrics (both apps, parallel)

```
mcp_anypoint-connect_get_memory_metrics(environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Heap used vs committed vs max
- GC count and time (high GC → memory pressure)
- Thread count (monitor for thread leaks)

### 1f. Worker Metrics (parallel)

```
mcp_anypoint-connect_get_worker_metrics(environment: "<ENV>", hoursBack: <N>)
```

**What to extract:**
- Per-replica request distribution (detect load imbalance)
- Per-replica latency (identify unhealthy replicas)

---

## Step 2: Deployment & Change Context

### 2a. Audit Log

```
mcp_anypoint-connect_get_audit_log(hoursBack: 48, objectTypes: ["Application"], limit: 50)
```

**What to extract:**
- Recent deploys: app name, version, timestamp, success/failure
- Who deployed (userName)
- Failed deploys (artifact not found, etc.)
- **CRITICAL**: Convert epoch timestamps to human-readable and check if any deploy overlaps with error windows

### 2b. App Status (both apps)

```
mcp_anypoint-connect_get_app_status(appName: "<YOUR_PAPI_APP>", environment: "<ENV>")
mcp_anypoint-connect_get_app_status(appName: "<YOUR_SAPI_APP>", environment: "<ENV>")
```

**What to extract:**
- Deployment status (APPLIED vs STARTED)
- Artifact version (verify expected version is running)
- Replica states (STARTED, PENDING, STARTING, FAILED)
- Replica scheduling issues (Insufficient CPU, node taints)
- vCores allocation

### 2c. Recent Code Changes (CHANGELOG)

Read the project CHANGELOG to understand what changed in the currently deployed and recent versions:

```
view_file(AbsolutePath: "<project_root>/CHANGELOG.md", StartLine: 1, EndLine: 50)
```

**What to extract:**
- What changed in the **currently running version** (match with artifact version from 2b)
- Changes in the 2-3 previous versions (in case a recent deploy introduced a regression)
- New flows, modified DWL transforms, scheduler changes, dedup logic changes
- Any config-only changes (yaml files) that wouldn't trigger a version bump

**How to use this context:**
- If errors reference a specific flow, check if that flow was modified in a recent version
- If error patterns changed after a deploy, the CHANGELOG tells you exactly what code changed
- If dedup-related issues appear (records skipping or not skipping), check if hash fields were modified
- Correlate the CHANGELOG entries with error patterns from Step 1b to narrow root cause

---

## Step 3: Deep Dives (Conditional)

Only do these if Step 1-2 reveal issues:

### 3a. If PAPI errors reference SAPI 500s

```
mcp_anypoint-connect_get_logs(appName: "<YOUR_SAPI_APP>", environment: "<ENV>", search: "<endpoint>", lines: 200)
```

Check if SAPI logged errors for the same endpoint. If SAPI shows 0 errors, the 500 came from the **downstream system** (e.g., NetSuite, Salesforce), not from the SAPI itself.

### 3b. If error spikes correlate with deploys

Compare error spike timestamps with audit log deploy timestamps. If a deploy occurred during the error window, that's likely the root cause (rolling deploy causing transient failures).

### 3c. If performance degradation is found

```
mcp_anypoint-connect_get_metrics_timeseries(environment: "<ENV>", appName: "<app>", hoursBack: <N>, granularity: "5m")
mcp_anypoint-connect_get_memory_timeseries(environment: "<ENV>", appName: "<app>", hoursBack: <N>, granularity: "5m")
```

Look for:
- Response time spikes correlating with memory/GC spikes
- Gradual heap growth (memory leak)
- Traffic spikes preceding latency increases

### 3d. If WARN logs are elevated

Download WARN-level logs to check for:
- **Salesforce streaming 403s**: Normal reconnect cycle, no action needed
- **Recursive flow-ref warnings**: Review flow for bounded termination
- **HTTP body ignored warnings**: Incorrect HTTP method + body combination

```
mcp_anypoint-connect_get_logs(appName: "<app>", environment: "<ENV>", level: "WARN", lines: 100)
```

---

## Step 4: Cross-System Correlation

This is the most important analytical step. Connect the dots:

### Known Error Patterns

| PAPI Error | SAPI Behavior | Root Cause | Action |
|------------|---------------|------------|--------|
| `HTTP:INTERNAL_SERVER_ERROR` on SAPI endpoint | SAPI has 0 errors | Downstream system returned 500 | Check downstream system |
| `HTTP:INTERNAL_SERVER_ERROR` on SAPI endpoint | SAPI also has errors | SAPI code bug or config issue | Debug SAPI flow |
| `HTTP:TIMEOUT` on SAPI endpoint | SAPI shows slow responses | Downstream system slow or SAPI overloaded | Check SAPI metrics + timeouts |
| `CUSTOMER:NOT_FOUND` | N/A | Business error — customer not synced yet | Check entity sync timing |
| `Connection was lost` (SF streaming) | N/A | SF CometD session expired | No action — auto-recovers |
| `Failed after 0 retries` | Companion to other errors | Retry exhaustion log — look for the actual error | Find the preceding error |

### Log Retention Gaps

> **IMPORTANT**: SAPI log retention is typically shorter than PAPI because SAPI may have DEBUG-level HTTP logging enabled (66%+ noise). If SAPI logs don't cover the error window, note this in the report.

### Correlation Approach

1. Get the **time window** of PAPI errors
2. Check if SAPI logs **cover that window** (compare log time ranges)
3. Check if any **deploys** occurred during that window (audit log)
4. If SAPI has 0 errors → downstream system caused the 500
5. If SAPI also has errors → SAPI is the root cause
6. If a deploy overlaps → rolling deploy caused transient failures

---

## Step 5: Report Generation

Generate the report as an artifact at the standard path. Use the following structure:

```markdown
# Production Log Analysis — PAPI + SAPI (Last <N>h)

**Period:** <start> → <end>
**Apps analyzed:** <YOUR_PAPI_APP>, <YOUR_SAPI_APP>

## Health at a Glance
| Metric | PAPI | SAPI |
|--------|------|------|
| Total entries | ... | ... |
| Error rate | ... | ... |
| Avg response time | ... | ... |
| p95 latency | ... | ... |
| Heap used / max | ... | ... |
| Replicas | ... | ... |

## Performance Summary
- Request volumes, response times, percentiles
- Outbound call patterns
- Memory and GC trends

## Error Analysis
- Each error group with: count, window, affected flows, root cause
- Cross-system correlation (PAPI ↔ SAPI ↔ downstream)
- Sequence diagram or ASCII flow showing the error path

## Activity Patterns
- Top log patterns and what they indicate
- Scheduler execution confirmation
- Filtered/skipped records

## Deploy Activity
- Recent deploys with timestamps and outcomes
- Any correlation with errors

## Recommendations
- Prioritized actions (🔴 🟡 🟢)
```

---

## Key Facts Reference

### App Architecture
- **PAPI** → HTTP → **SAPI** → HTTP → **External Systems**
- PAPI never calls downstream systems directly
- SAPI proxies errors from downstream — a SAPI 500 usually means the external system returned 500

### Common Gotchas

#### Log Retention & Coverage
1. **SAPI logs are much shorter than PAPI** — SAPI may have DEBUG-level HTTP request/response logging enabled, which generates 66%+ noise. This fills the log buffer faster, so SAPI typically retains only ~14h vs PAPI's 24h+. Always check the `Time range` in log stats before assuming you have coverage.
2. **SAPI errors won't show downstream errors** — When an external system returns a 500, the SAPI forwards it to PAPI as a 500 response. The SAPI treats this as a "successful" proxied response and logs it at INFO level, NOT ERROR. So `analyze_errors` on the SAPI will show 0 errors even though the PAPI saw 500s.
3. **`download_logs` vs `get_logs`** — Use `get_logs` for quick checks (returns structured JSON, searchable). Use `download_logs` for time-window filtering and level filtering. `get_logs` returns the most recent N entries regardless of time.

#### Audit Log Timestamps
4. **Audit log timestamps are epoch milliseconds** — The `timestamp` field in audit entries is Unix epoch in ms (e.g., `1774546428281`). You must convert these to compare with error windows. Don't confuse with the human-readable `lastModifiedDate` on the deployment response.
5. **`APPLIED` vs `STARTED`** — `get_app_status` may return `APPLIED` during a rolling deploy. This does NOT mean the app is down — the old replicas continue serving. Only `FAILED` status indicates an actual problem. Check individual replica states for the real picture.
6. **Replica state snapshots are point-in-time** — The audit log captures replica states at deploy time. `PENDING`/`STARTING` replicas in the audit log may have already resolved. Always cross-reference with a fresh `get_app_status` call.

#### Error Analysis Traps
7. **"Failed after 0 retries" is NOT the root error** — This is the retry-exhaustion summary log. The actual error is in a separate log entry with the same correlation ID, usually immediately before or after. Count these separately from the real errors to avoid double-counting.
8. **Error logging entries are INFO, not ERROR** — After the PAPI logs the ERROR, it may call an error logging flow to write to an external system. This second log entry appears at INFO or ERROR level as a `DefaultExceptionListener` entry. Don't count it as a separate error.
9. **Error groups may double-count** — `analyze_errors` groups by message pattern. A single transaction can produce both a structured logger ERROR entry AND a `DefaultExceptionListener` entry. These are the same error seen by different loggers.

#### Metrics Interpretation
10. **Metrics are per-environment, not per-app by default** — `get_metrics` and `get_performance_metrics` return all apps in the environment. Filter by `appName` when investigating a specific app.
11. **SAPI appears to have low request counts** — SAPI handles internal PAPI→SAPI traffic only. Don't expect external traffic volumes. Compare SAPI request counts to PAPI's outbound request counts for consistency.
12. **p95/p99 can be misleading with low volumes** — If an app handles only 10 requests in the window, a single slow request will skew p99 to the max latency. Always check request count alongside percentiles.

#### Cross-System Debugging
13. **Correlation IDs cross the PAPI→SAPI boundary** — PAPI sends `X-Correlation-Id` on every SAPI request via HTTP request default headers. The SAPI's `http:listener` automatically adopts this as its `correlationId`. Use the correlation ID to trace a request end-to-end across both apps.
14. **SAPI `search` on endpoint names** — When searching SAPI logs for a specific endpoint, use partial matches (e.g., `get_logs(search: "ns-Invoice")`) without the trailing 's' to catch both singular and plural references.
15. **SF streaming drops cascade** — When Salesforce streaming drops (HTTP 500/503 on CometD), multiple listener flows drop simultaneously because they share the same SF connection. A single SF hiccup can produce 3-5 `Connection was lost` ERROR entries across different flows within the same second. These are ONE incident, not separate ones.

#### Build & Deploy
16. **Failed deploys leave ghost versions** — A failed deploy (e.g., artifact not found in catalog) creates an audit entry with `failed: true` but the previous version keeps running. The `desiredVersion` in the response may differ from `lastSuccessfulVersion` — always check `lastSuccessfulVersion` for what's actually running.

### Common False Alarms
1. **SF streaming 403 + reconnect** — Normal CometD lifecycle, ~200+ WARN entries per day
2. **Business filter logs** (e.g., "field X is blank") — Expected filter, not an error
3. **"User license is not Salesforce"** — Expected filter for non-SF users
4. **"response success. retries: 0"** — Healthy SAPI response (can be 49%+ of all PAPI logs)
5. **"Body is ignored since the HTTP Method is between the empty body methods"** — GET requests with a body — harmless, the body is just ignored
6. **"Found a possible infinite recursion involving flows named '...'"** — Mule runtime detects recursive flow-refs. If this is a pagination pattern that terminates when there are no more pages, it's bounded but Mule can't statically verify that
7. **`OS:KEY_NOT_FOUND` on cache stores** — Cache misses in cache-aside patterns. If the flow has a fallback path that queries the system of record on miss, this is expected behavior, not a real error. Fix with `<os:default-value>#[null]</os:default-value>` to prevent the error entirely.
