# See Mule Skills in action

These two journeys show what a Mule developer actually receives. They are grounded in the sample
projects shipped by [`mule-build` at `5b252ed`](https://github.com/Avinava/mule-build/tree/5b252edd1d36b1d91d9f1f8b682fbc6038eaf0f1/examples/sample-orders-system-api)
and [`mule-lint` at `b828113`](https://github.com/Avinava/mule-lint/tree/b8281135ced9d68846b39e19b578710b0fe8e8e0/examples/sample-orders-system-api),
using `mule-lint@2.0.0` and `mule-build@3.0.0`, measured on 2026-10-03 with Java 17.
The samples remain at these exact commits; tool upgrades do not silently change the source baseline.

This is not a gallery where every skill is forced to produce a file. Some skills change source or
tests; some return a decision, review, diagnosis, or operational assessment. Each journey says what
was observed from the tools and shows the representative handoff a developer should expect.

## Journey 1: make a small Mule change and prove what is ready

**Developer request**

```text
Add currency: "USD" to the order returned by the sample flow. Extend the existing MUnit test,
validate and package the application, and review the result. Do not commit or deploy anything.
```

### Why these skills participate

`mule-development` owns the DataWeave change, `mule-testing` owns the behavior assertion,
`mule-build` owns local readiness, tests, and packaging, and `mule-review` turns the evidence into a
readiness verdict. API design is not added because this sample has no RAML or OAS contract to change.
Documentation, operations, and troubleshooting are not added because the request makes no document
stale and provides no runtime incident or telemetry.

### Source and test change

The pulled baseline contained one Mule flow, one MUnit suite, one executable test, and two
assertions. In an isolated copy of the sample, the returned value and its test became:

```dataweave
output application/json
---
[{ id: "ORD-1001", status: "READY", total: 42.50, currency: "USD" }]
```

```xml
<munit-tools:assert-that
    doc:name="Currency Is Stable"
    expression="#[payload[0].currency]"
    is="#[MunitTools::equalTo('USD')]" />
```

That is the intended production-and-test delta. It does not, by itself, prove that the application
is releasable.

### Observed validation evidence

| Gate | Observed result | Product meaning |
| --- | --- | --- |
| Project inventory | 1 flow, 1 MUnit suite, 1 test, now 3 assertions | The change has a focused test target |
| Embedded-expression check | Passed | No malformed embedded expression was found |
| Build doctor for `test` | Passed | Maven, the POM, Mule/MUnit plugins, source layout, and a compatible local runtime were detected |
| Secure-property enforcement | Passed; 1 Mule file checked | The documented property-name/reference checks found no violation; this is not a general secret scan |
| `mule-lint@2.0.0` | Complete scan, exit `1`: 1 error, 6 warnings, 5 information findings | The sample still has review findings, including no flow error handler |
| Focused MUnit selector | Exit `1`: no matching suite found | The requested suite/test selector was not resolved; the full run below executed the test |
| Full MUnit run | Passed: 1 run, 0 failures, 0 errors, 0 skipped | The test, including the added currency assertion, executed successfully |
| Normal package | Passed with tests enabled; 1 test passed and a JAR was produced | Local test and packaging evidence is available; lint findings still need review |

The focused command used `--suite orders-test-suite --test list-orders-flow-returns-an-order`.
It did not select a suite. Running `test` without selectors and then `package` both succeeded with
tests enabled. The selector result remains a separate limitation; it does not erase the successful
full-suite evidence. No tests-skipped package was used. The default lint scan evaluated no configured
quality gate; its complete execution and non-clean findings are separate facts.

### Representative developer handoff

```text
Outcome: Implemented in an isolated copy of the pinned mule-build sample.

Changed:
- orders.xml returns currency: "USD".
- orders-test-suite.xml asserts payload[0].currency == "USD".

Evidence:
- Embedded-expression and secure-property checks passed.
- mule-lint is non-clean: 1 error, 6 warnings, 5 information findings.
- Focused MUnit selection found no suite; the full run passed 1 test with no failures or skips.
- Normal packaging passed with tests enabled and produced a JAR with embedded coordinates and SHA-256.

Review verdict: Not ready to release. Test and packaging evidence passed; clear or disposition the
lint findings before treating the artifact as a release candidate.

Release actions: None. No commit, tag, publish, or deployment was performed.
```

The useful output here is not a green-looking artifact. It is a bounded change plus enough evidence
for a developer to know exactly what passed, what did not, and what decision remains.

## Journey 2: review a deliberately flawed Mule project without changing it

**Developer request**

```text
Review this Mule application for correctness and release risk. Report only; do not edit files or
change repository or runtime state.
```

The [`mule-lint` sample](https://github.com/Avinava/mule-lint/tree/b8281135ced9d68846b39e19b578710b0fe8e8e0/examples/sample-orders-system-api)
is intentionally flawed so a review can demonstrate prioritization instead of manufacturing a
perfect result.

### Observed tool evidence

`mule-lint@2.0.0` returned a complete report-v1 scan of three Mule files and exited `1` with:

```text
Errors: 1    Warnings: 10    Info: 9
```

No configured quality gate was evaluated in this default scan. The non-zero exit reflects the
error finding; execution completeness is reported separately.

The release-blocking error is at `src/main/mule/orders-api.xml:31`: flow
`get-order-by-id-flow` has no error handler (`MULE-003`). Warnings also cover correlation
handling, HTTP status handling, rate limiting, missing TLS context on an HTTPS backend,
unversioned listener paths, missing API specification evidence, inbound authentication
evidence, and missing environment properties. Informational findings include missing
component descriptions, Try-scope guidance around HTTP requests, a missing health endpoint, and
`TEST-001`: four production flows with no executable MUnit tests.

### Representative review handoff

```text
[High] Add an explicit error-handling contract for get-order-by-id-flow

Evidence: mule-lint reports MULE-003 at src/main/mule/orders-api.xml:31 because the flow has no
error handler.

Impact: connector, transformation, or lookup failures can escape without the API's intended status,
payload, logging, and correlation behavior. Release behavior is therefore not established.

Fix direction: define or reference the project's approved error handler, then add MUnit coverage for
the expected error event and rerun lint plus the focused and full test gates.
```

The review would then list the ten warnings in priority order, distinguish standards findings from
demonstrated runtime defects, and state its coverage: repository XML and static rules were inspected;
runtime logs, metrics, deployment state, and API contract behavior were not available. No source,
comment, commit, PR, or runtime state is changed by the review.

## What these journeys do not claim

- They do not demonstrate API contract design because neither selected journey contains an API
  specification that needs a product decision.
- They do not invent an operational health report or root-cause analysis without runtime evidence.
- They do not treat a generated JAR as proof that tests passed or a deployment was authorized.
- They do not imply that every skill creates a file. See the [skill catalog](skills.md) for each
  skill's default effect and expected handoff.

For reusable request patterns and ownership boundaries, continue to the
[workflow guide](workflows.md).
