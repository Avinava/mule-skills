# Behavior model for MUnit tests

Use this reference after inspecting the production path and existing test conventions. It is the
bundled fallback for the canonical `MSTD-TEST-001` testing guidance exposed by mule-lint.

## Contents

1. [Behavior ledger](#behavior-ledger)
2. [Invariant-class mapping](#invariant-class-mapping)
3. [Fixtures from production shapes](#fixtures-from-production-shapes)
4. [Pass conditions for intermittent faults](#pass-conditions-for-intermittent-faults)
5. [Evidence that tests ran](#evidence-that-tests-ran)
6. [Mock, assert, verify, or spy?](#mock-assert-verify-or-spy)
7. [Failure classification](#failure-classification)
8. [Coverage and Test Recorder](#coverage-and-test-recorder)
9. [Privacy boundary](#privacy-boundary)

## Behavior ledger

Create one row per material behavior. Omit cases the implementation cannot exercise and record why.

| Case | Trigger and event | Dependency/state setup | Observable outcome | Required/forbidden interactions | Failure/state disposition |
| --- | --- | --- | --- | --- | --- |
| Success | Caller-faithful payload, attributes, variables, and media type | Normal dependency response | Contracted payload, attributes, variables, or source result | Expected boundary calls; forbidden alternate calls | State committed and acknowledgement consistent with the source |
| Alternate | Evidence-backed branch input | Branch-specific setup | Alternate contracted result | Only branch-appropriate calls | Branch-specific state and delivery outcome |
| Invalid or empty | Boundary value with faithful type | No irrelevant dependency setup | Validation or mapped error | Side effects must not occur when validation precedes them | Caller/source receives the designed terminal outcome |
| Dependency failure | Valid event | Typed dependency error or timeout | Mapped error, fallback, or propagation | Retry/fallback calls match policy | Retryable or terminal disposition remains executable |
| Retry exhaustion | Valid event | Dependency fails for every permitted attempt | Exhausted error or governed terminal result | Attempt count and forbidden post-success work | No false acknowledgement or partial committed state |
| Replay or recovery | Duplicate or resumed event | Existing state, watermark, or prior side effect | Idempotent result or documented duplicate behavior | No unintended duplicate side effect | State remains recoverable after interruption |

## Invariant-class mapping

| Class | Test evidence |
| --- | --- |
| Class A — Value contracts | Shape, type, media type, nullability, serialization, and fixture fidelity at the next consumer |
| Class B — Expression embedding | The executed Mule XML evaluates the complete embedded expression; parser-only checks are supplementary |
| Class C — Contract authority | The bound API/event contract, reachable route, and caller/source outcome agree |
| Class D — Failure disposition | Error type, retry selection, exhaustion, terminal handling, acknowledgement, and attribution are observable |
| Class E — State and idempotency | Store keys, watermarks, replay, duplicates, failed writeback, and recovery preserve the intended invariant |

Apply cross-cutting gates whenever relevant: safe configuration, authentication and authorization,
capacity and lifecycle, transactions and delivery, privacy and observability, and release validation.

## Fixtures from production shapes

Derive each fixture's structure from how the real caller or source sends data, then replace every
value with synthetic data. A field the producer sends as a present empty key behaves differently
from an absent field (`default` does not apply to the empty value), so a fixture that omits it can
pass while production fails. When a fix passed tests and still failed in production, compare the
fixture's shape to the production shape before writing another fix. Record the shape variants
(absent, null, empty, alternate nesting) as ledger rows.

## Pass conditions for intermittent faults

For a fix to an intermittent or periodic fault, the pass condition is the fault's own trigger
occurring and the behavior holding: for example, surviving the reconnect, token expiry, or
redelivery that caused it. A run with no errors at low volume, or before the trigger has fired, is
not evidence. Where MUnit cannot reproduce the trigger, state the condition to observe after
release and leave the case open until it is met.

## Evidence that tests ran

Before trusting a result, confirm MUnit booted and executed a nonzero number of tests for the
selection, on the JDK the project targets, with one MUnit version across plugin, runner, and tools.
When tests cannot run, record the substitute evidence (DataWeave fixture tests, a harness that runs
the changed flow against a stub) as such; it does not make the change tested.

## Mock, assert, verify, or spy?

- **Mock a boundary** when the test owns the local decision but the real dependency is nondeterministic,
  slow, unavailable, or outside the unit boundary.
- **Do not mock the subject**: transformations, routers, state decisions, retry/error strategy, and
  contract mapping under test must execute.
- **Assert outcomes** visible to the caller, source, state store, or next governed boundary. Include
  value type and media type when downstream behavior depends on them.
- **Verify interactions** when calling or not calling a dependency is itself part of the contract.
- **Spy sparingly** for meaningful before/after evidence that cannot be observed through a stable
  outcome. Internal processor sequencing is usually a brittle assertion.

Selectors should identify one intended call using stable processor identity and evidence-backed
inputs. A mock that matches every operation of a connector can make the wrong branch pass. Keep
selector values in the test project; inventories and reusable documentation should report selector
attribute names only.

## Failure classification

Before changing a failing test, choose the evidence-backed class:

| Class | Typical evidence | Correct response |
| --- | --- | --- |
| Product regression | The current contract and ledger still require the asserted behavior | Fix production source through `mule-development`, then retain the assertion |
| Stale expectation | An authorized behavior or contract change makes the old outcome obsolete | Update ledger, test, contract, and documentation together |
| Unfaithful setup | Event shape, media type, attributes, variables, or fixture differ from the real caller | Repair the setup or fixture |
| Mock mismatch | Selector misses the intended boundary call or hides another call | Narrow or correct the selector and verify interactions |
| Environment/build failure | Maven, Java, dependency resolution, plugin, or runtime fails before behavior executes | Route execution diagnosis through `mule-build` or `mule-troubleshooting` |
| Flaky nondeterminism | Time, ordering, random data, concurrency, or external state changes repeated outcomes | Remove uncontrolled dependency or assert the actual deterministic contract |

Never make a test green by removing meaningful evidence, broadening a mock without justification,
ignoring the test, or lowering a required gate.

## Coverage and Test Recorder

Coverage can reveal an unexecuted processor or branch, and Test Recorder can accelerate observation
of an existing path. Neither establishes correct inputs, outcomes, errors, state transitions, or
delivery semantics. Review generated tests as untrusted scaffolding: replace captured sensitive data,
remove incidental assertions, restore faithful event construction, and add boundary/error cases from
the behavior ledger. Use a project-owned threshold only when the repository defines one; do not
invent a universal percentage.

## Privacy boundary

Fixtures and examples must be synthetic and schema-faithful. Never preserve secrets, tenant or
organization identifiers, private endpoints, personal data, raw production payloads, correlation
identifiers, incident fingerprints, or names and tuning values copied from another project.
