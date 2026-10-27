# Conditional signals and focused retrieval

## Contents

- [Conditional signals](#conditional-signals)
- [Focused retrieval](#focused-retrieval)
- [Alert design](#alert-design)

Read this after broad collection when a specific signal (latency, replica imbalance, error burst,
memory, CPU, back pressure, warnings) needs a deeper check, or when focused log or time-series
retrieval is justified.

## Conditional signals

- **Latency:** Pull time series for the affected app and compare latency with traffic, outbound
  duration, CPU, memory, GC, and replica balance. Use `groupBy: "route"` to find failing or slow
  routes; outbound routes are labelled, while inbound routes may be unlabelled.
- **Replica imbalance:** Compare workers with `groupBy: "worker"` before attributing a symptom to
  the whole application.
- **Error bursts:** Compare the burst with schedulers, batch instances, queue depth, retries,
  dependency limits, and deployments.
- **Memory:** Judge pressure by the old-generation pool, not total heap: compare its peak with its
  limit (`oldGenPeakRatio`) and trend its baseline across days with the `memory` signal in 1h or 1d
  buckets. A total-heap sawtooth is normal. A rising old-generation floor is a leak hypothesis, not
  proof. Frequent old-generation collections (`oldGenGcCount`, `oldGenGcTimeMs`) that reclaim little
  suggest pressure; also check a single replica diverging from peers.
- **CPU and host memory:** Compare system and process CPU load (0–1) and average free physical
  memory per worker before attributing latency to the application itself.
- **Back pressure or rate limits:** Estimate effective concurrency from flow limits, source
  consumers, batch-job concurrency, parallel scopes, replicas, and dependency quotas.
- **Warnings:** Sample by pattern and verify recovery or impact. Do not declare a reconnect,
  recursive-flow warning, ignored body, or cache miss harmless without checking the actual outcome.

## Focused retrieval

Use focused retrieval only after broad collection identifies a reason:

```text
mcp_anypoint-connect_get_logs(appName: "<APP>", environment: "<ENV>", search: "<SAFE_TERM>", lines: <LIMIT>)
mcp_anypoint-connect_get_metrics_timeseries(environment: "<ENV>", appName: "<APP>", hoursBack: <HOURS>, signal: "traffic", granularity: "5m")
mcp_anypoint-connect_get_metrics_timeseries(environment: "<ENV>", appName: "<APP>", hoursBack: <HOURS>, signal: "memory", granularity: "1h")
```

Choose `signal` from `traffic`, `latency`, `memory`, `cpu`, or `gc`. Use `1m` or `5m` granularity for
an incident window and `1h` or `1d` for multi-day baseline trends. Use
`mcp_anypoint-connect_raw_amql_query` only when the shaped tools cannot answer the question; it
returns at most 2000 rows.

Search with the least sensitive stable term that identifies the flow or operation. Do not expose
raw results when a count and sanitized pattern are sufficient.

## Alert design

When a health review recommends or reviews alerts, judge each rule by how it behaves at the app's
real traffic, not by its wording:

- **Ratio plus a floor, evaluated often.** A pure count rule over a long window pages a total outage
  late at low volume. Evaluate every few minutes on a minimum count and a failure ratio.
- **Alert on silence.** Add a "no successful call for N minutes" rule, with N above the longest
  natural gap in traffic. Silence is how a stalled source or a lost subscription shows up.
- **Do not page on benign lines.** A periodic connector reconnect ERROR is expected; alert on its
  rate changing or on a missing recovery instead.
- **Memory on sustained old-generation use.** A threshold near the GC sawtooth flaps. Check whether
  the threshold field is a fraction or a percentage.
- **Tag probes** so smoke tests and watch traffic neither page nor skew the counts.
- **Prove the rule can fire.** A rule or watch script that cannot match reports green forever; test
  it against live data.
