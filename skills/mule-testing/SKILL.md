---
name: mule-testing
description: Create, repair, and refactor behavior-focused MUnit tests for MuleSoft Mule 4 applications, including event setup, fixtures, mocks, spies, assertions, error expectations, and test-only build configuration. Use when adding missing MUnit coverage, diagnosing or fixing a failing MUnit test, preserving behavior during a Mule change, or improving test fidelity. Route production Mule source changes to mule-development and execution-only, packaging, or release work to mule-build.
---

# Mule Testing

Create MUnit evidence for the current project's actual behavior. Treat coverage as a navigation aid,
not the definition of correctness, and keep reusable guidance free of project identity and private
data.

## Establish the authority and boundary

1. Read repository instructions, `pom.xml`, `mule-artifact.json`, the production flow under test,
   its callers or source, effective error handling, relevant contracts, and existing MUnit suites.
2. Read the shared
   [mule-lint standards protocol](../mule-development/references/mule-lint-standards.md), then load
   `MSTD-TEST-001` and `mule-lint://docs/testing` when the MCP resource is available. If it is not,
   use [Behavior model](references/behavior-model.md) as the bundled minimum.
3. Use the canonical Classes A–E from
   [mule-development](../mule-development/references/invariant-classes.md) for value, embedded
   expression, contract, failure, and state behavior. Apply relevant security, capacity, delivery,
   privacy, and validation gates.
4. Keep production changes outside this skill. If a correct test exposes a product defect, report
   it and route the source fix through `mule-development`; do not weaken the test to preserve the
   defect.

Never copy application names, endpoints, payloads, identifiers, schedules, volumes, incident data,
topology, or tuning values from another project. Use only current-project evidence in current-project
tests, and use neutral synthetic values in reusable examples.

## Inventory before editing

Run the read-only inventory from this skill directory:

```bash
python3 <skill-root>/scripts/inventory_munit.py <project-root> --pretty
```

`<skill-root>` is `${CLAUDE_PLUGIN_ROOT}/skills/mule-testing` for the Claude plugin and
`.agents/skills/mule-testing` when vendored into a project. The inventory reports structure and names, not
fixture contents or selector values. A valid Mule project with no tests is a successful inventory
with an evidence gap; a non-Mule target or invalid argument exits with status 2.

Reconcile the inventory with direct source inspection. It uses name mentions only as a heuristic for
flow-to-test mapping and never proves behavioral coverage.

## Build a behavior ledger

Before writing tests, record each material case using the template in `references/behavior-model.md`:

- trigger or caller and input-event shape;
- dependency and state preconditions;
- expected payload, attributes, variables, error, and source/caller outcome;
- required interactions and interactions that must not occur;
- retry, redelivery, acknowledgement, idempotency, and state effects where applicable.

Cover cases by risk and behavior, not by one-test-per-flow or a universal percentage. Consider
success, meaningful alternatives, empty or invalid input, dependency failure, retry exhaustion,
terminal disposition, replay, and recovery only when the implementation can exercise them.

## Author or repair the tests

1. Reuse the project's established suite layout, naming, fixture style, namespace versions, and
   MUnit plugin configuration.
2. Construct the event the real caller or source supplies: payload value and media type, attributes,
   variables, correlation context, and any required source metadata.
3. Mock stable boundaries such as HTTP, database, queue, file, or external flow dependencies when
   isolation is intended. Do not mock the transformation, routing, state decision, or error behavior
   being tested.
4. Make selectors discriminate the intended call using stable processor identity and inputs. Avoid
   a broad mock that can hide an unexpected branch.
5. Assert observable behavior: output values and types, variables or attributes, error type and
   disposition, state changes, and source/caller outcomes. Verify important boundary calls and use
   negative verification when an interaction must not occur.
6. Use spies only when before/after observation is the least coupled way to establish a behavior;
   do not substitute internal-step assertions for an observable outcome.
7. Keep fixtures synthetic, minimal, schema-faithful, and free of secrets, raw production payloads,
   tenant details, private hosts, personal data, and identifiers copied from elsewhere.

When repairing a failure, classify it before editing: product regression, stale expectation,
unfaithful event or fixture, mock mismatch, environment/build failure, or flaky nondeterminism. Change
only the layer supported by evidence. Never delete an assertion, broaden a mock, ignore a test, or
lower a gate merely to make the suite pass.

## Prove the toolchain runs

A green result means nothing until MUnit has booted and executed tests.

- Confirm the report shows a nonzero count of executed tests for the selection. Zero tests, or a
  run that ends before the suites load, is a toolchain failure, not a pass.
- Use one MUnit version for `munit-maven-plugin`, `munit-runner`, and `munit-tools`. A plugin
  property that moves while the two dependencies stay hardcoded leaves an old runner that may not
  boot. Java support is version-specific (for example, Java 17 needs MUnit 3.1.0 or later at the
  time of writing); confirm the supported pair through
  [`mule-dependencies`](../mule-dependencies/SKILL.md). The mule-build `check_compatibility` tool
  (`MB-TC-007` for version skew, `MB-TC-002` for the Java 17 minimum) and mule-lint (`TEST-002`)
  both check MUnit versions; run them and resolve their findings.
- `mule-build` `run_tests` runs on the server's JDK, not necessarily the project's. Read the JDK
  the run reports and confirm it is the one the project targets.
- When the production runtime cannot run tests locally, commit a test-only Maven profile that sets
  the MUnit version, a test runtime, a JDK enforcer rule, and placeholder values for secure keys.
  Prove the profile does not change what ships: package without it before and after the change and
  compare the deployable contents (Mule XML, DataWeave, resources, `mule-artifact.json` and the
  resolved dependency set). The embedded POM and build timestamps change with any POM edit, so a raw
  digest comparison is not the test; any other difference is.
- If tests cannot run, say so. Name the substitute evidence, such as DataWeave fixture tests or a
  harness that runs the changed flow against a stub, and its limits. Never call the change tested.

## Validate

Run the narrowest deterministic test first, then the repository-required broader gate:

1. Prefer `mule-build` `run_tests` with `cwd` and an exact suite, test, or tag selection.
2. Otherwise use the project's established Maven or wrapper command and its pinned profile.
3. Inspect the MUnit report and first actionable failure, not only the process exit status, and
   confirm the executed test count is nonzero.
4. Run the affected suite, then the complete required test/package gate for release scope.
5. Re-run the inventory and inspect the final diff for ignored tests, over-broad selectors,
   production-source edits, generated reports, fixture leakage, and unrelated changes.

Do not use `-DskipTests` or equivalent to validate a test change. Coverage and Test Recorder can
identify unexercised paths, but no fixed percentage proves the behavior ledger is complete.

For black-box tests against a running API, outside MUnit, read
[API functional tests](references/api-functional-tests.md).

## Report

Return:

1. behavior cases added, repaired, or still missing;
2. suites, tests, fixtures, and test-only configuration changed;
3. focused and full commands or tools run, with results and report paths;
4. failure classification when a test was repaired;
5. skipped checks, environment limitations, production defects, and remaining evidence gaps.

## Gotchas

- A mock mismatch, an unfaithful event, or a build failure says nothing about the product; a correct
  failing test can support a defect hypothesis.
- Fixtures shaped for Studio convenience can hide production shapes. Cover normal and representative
  adverse inputs, built from real production shapes such as a field sent as an empty key rather
  than omitted.
- A fix for an intermittent fault passes only when the fault's own trigger passes, not when a
  quiet run shows no errors.
- A zero-test run exits green. Check the executed count.
- Do not use `-DskipTests` to validate a test change, and do not read a green exit status as proof.
  Inspect the MUnit report and the first actionable failure.
- No coverage percentage proves the behavior ledger is complete.
