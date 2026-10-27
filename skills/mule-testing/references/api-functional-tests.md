# API functional tests

Use this reference for black-box tests that call a running Mule API over HTTP, as a deployed or
locally run application, independent of the test runner. MUnit tests the flow from inside the
runtime; functional tests check what a consumer actually receives. Both need the behavior ledger
from [Behavior model](behavior-model.md).

## Endpoint allowlist

Test only endpoints the application actually serves. Build the list from two sources:

- the HTTP listeners in the Mule XML (base path, port property, and listener path);
- the bound API contract (the RAML or OAS that `apikit:config` references, or its published pin).

Resolve routing before comparing them. A listener such as `/api/*` that hands off to
`apikit:router` serves the contract's resources beneath that base path, so expand each contract
resource and method under the listener's path, then confirm APIKit dispatches it to an implemented
flow. Plain listeners without a router contribute their own paths. An endpoint in the contract with
no reachable implementation, or a listener path absent from the contract, is a finding to record,
not a test to write. Never add endpoints from memory, examples,
or another project.

## Configuration from the environment

- Read the base URL, client credentials, and tokens from environment variables or a local file
  outside the repository. Never write them as literals in test code, fixtures, or reports.
- Fail the run early with a clear message naming the missing variable, not its value.
- Keep one configuration per environment and refuse to run against an environment the run was not
  pointed at explicitly.

## Authentication and authorization cases

For each protected endpoint, cover both sides:

| Case | Expected |
| --- | --- |
| Valid credential with the required scope or role | The contracted success response |
| No credential | The contracted authentication failure, with no side effect |
| Invalid or expired credential | The contracted authentication failure, with no side effect |
| Valid credential without the required scope or role | The contracted authorization failure, with no side effect |

Confirm error bodies follow the contract's error envelope and carry no stack traces, internal
hosts, or credential material.

## Side-effect boundary

Before running, list which calls write to a real system (create, update, delete, publish, send)
and which only read. For each write:

- run it only against an environment where writes are allowed, with synthetic data that is
  identifiable as test data;
- record how the test cleans up or why the record can stay;
- never run writes against production unless the user approves that specific run.

Report the boundary with the results so a reader knows what the run changed.

## Discrepancies

When a response differs from the contract or the ledger, record the discrepancy: endpoint, request
shape, expected, actual. Do not change the application, the contract, or the assertion to make the
test pass. Route a product defect to `mule-development` and a contract question to the contract
owner.
