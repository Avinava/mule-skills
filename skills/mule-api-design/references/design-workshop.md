# Design workshop

Turn incomplete requirements into a small set of reviewable decisions. Do not interrogate the user with a
generic questionnaire; ask the highest-impact unresolved questions for the current consumer task.

## Evidence order

1. Repository instructions and the bound or published contract.
2. Consumer workflows, existing integrations, and user-provided requirements.
3. Organization governance profiles and documented conventions.
4. Explicitly labeled inference.
5. Recommendation.

An existing implementation is evidence of current behavior, not automatically the desired public design.

## First-pass questions

Cover only unresolved items: consumers/tasks; new, compatible, or breaking scope; resource and identifier
ownership; sensitive/expensive/eventually consistent data; retry behavior; long-running operations;
authentication/authorization; and authoritative format, asset, and governance profiles.

Ask at most three related questions in one round. Recommend the least surprising reversible choice. If an
answer is unavailable, record `Assumption`, its risk, and how to verify it.

## Decision ledger

| Decision | Chosen option | Alternatives | Evidence or rationale | Compatibility impact | Owner/status |
| --- | --- | --- | --- | --- | --- |
| Contract authority |  |  |  |  |  |

Include URI shape, method semantics, representation, errors, pagination, concurrency, idempotency,
security, versioning, and publication only when material.

## Resource and operation matrix

| Consumer task | Resource/URI | Method | Request | Success | Material errors | Security | Retry/state behavior |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

Authoring can start when the source of truth, primary resources, operation semantics, identifiers,
security boundary, compatibility posture, and material state/error behavior are explicit.
