# Report structure and diagnostic lessons

## Contents

- [Report structure](#report-structure)
- [Reusable diagnostic lessons](#reusable-diagnostic-lessons)

Read this when writing the final analysis, and when interpreting a recurring mechanism or deciding how
much weight a signal deserves.

## Report structure

Use this structure:

```markdown
# Runtime health analysis

**Window:** <START> to <END> <TIMEZONE>
**Scope:** <ROLE-BASED APPLICATION LIST>

## Assessment
One paragraph with current health, impact, and confidence.

## Coverage
Actual telemetry coverage and material gaps.

## Health signals
Comparable log, error, latency, memory, GC, and replica observations.

## Correlated incidents
Signature, affected path, count of unique transactions, evidence state, and user impact.

## Deployment and change context
Verified overlaps and what remains unproven.

## Actions
Prioritized immediate checks, durable improvements, owner role, and verification signal.

## Unresolved questions
Only questions whose answers would change the assessment.
```

State denominators and windows for every rate. Present percentile latency with request count. Keep
expected business filters separate from technical failures, and preserve an `Unresolved` state when
coverage cannot support attribution.

## Reusable diagnostic lessons

- Interpret recurring mechanisms through `mule-development` Classes A–E and its mandatory
  cross-cutting gates. Use source inspection or troubleshooting before turning an operational signal
  into a code conclusion.
- A retry-exhaustion summary is often secondary evidence; locate the underlying connector or
  business error with the same correlation ID.
- Structured logger and exception-listener entries can describe one failed transaction; deduplicate
  by correlation ID, flow, signature, and time before counting.
- A deployment overlapping an error spike is a hypothesis until lifecycle messages, replica state,
  version changes, or before/after behavior support it.
- Application status and replica state are point-in-time observations. Distinguish desired,
  transitioning, current, and last-successful versions when the API exposes them.
- Percentiles are unstable at low request counts. Always report the sample size.
- Correlation propagation must be verified in source or telemetry. Mule can adopt an inbound
  `X-CORRELATION-ID`, but outbound propagation depends on configuration.
- Default log level, custom error handling, and proxy behavior determine where a failure appears;
  absence from an error-grouping tool is not evidence of absence.
- The same error signature repeating every scheduler or poll cycle may be a dependency outage, a
  permanent/poison record without terminal disposition, or intentional indefinite retry of retryable
  errors. Hand off to troubleshooting Class D checks before assuming a terminal state is missing.
- Logged application version that does not match the packaged artifact makes before/after and
  deploy correlation unreliable—confirm version surfaces before attributing behavior to a release.
- High-volume cache-miss ERROR noise can mean Object Store miss handling treats expected misses as
  exceptional; confirm miss policy before scaling infrastructure.
- Do not recommend concurrency or pool numbers without measured traffic, replica count, and
  dependency capacity for this environment.
