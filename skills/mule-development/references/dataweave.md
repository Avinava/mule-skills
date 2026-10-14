# DataWeave design guidance

Use this reference when writing, reviewing, or debugging a transformation. It complements Class A
(value contracts) in [Invariant classes and cross-cutting gates](invariant-classes.md); read that
file when a transformation feeds a connector, a queue, or a response with its own contract.

## Contents

1. [Decide the contract first](#decide-the-contract-first)
2. [Null, empty, and missing](#null-empty-and-missing)
3. [Choosing map, filter, reduce, and built-ins](#choosing-map-filter-reduce-and-built-ins)
4. [Lookups and grouping](#lookups-and-grouping)
5. [Streaming and one-pass reads](#streaming-and-one-pass-reads)
6. [Decimals, dates, and time zones](#decimals-dates-and-time-zones)
7. [Anti-pattern table](#anti-pattern-table)
8. [Module extraction rule](#module-extraction-rule)
9. [Verify against the installed version](#verify-against-the-installed-version)

## Decide the contract first

Before writing the body, name the consumer and what it accepts: media type, root shape (object or
array), required fields, nullability, and whether it reads the value once or many times.

- Declare `output` explicitly when inputs carry different media types, when inference could differ
  from what the consumer needs, or when a specific writer must be guaranteed.
- Declare the root shape on purpose. An empty input must still produce a valid root of that shape
  (an empty array, not null) unless the consumer defines another rule.
- Keep property names, casing, and ordering stable when a downstream system compares or signs the
  payload.

```dataweave
%dw 2.0
output application/json
---
(payload.items default []) map (item) -> {
  id: item.id,
  label: item.label
}
```

## Null, empty, and missing

Treat three states separately: the key is absent, the key is present with null, and the value is
empty (empty string, empty array, empty object). Each can mean something different to the consumer.

| Intent | Mechanism |
|---|---|
| Supply a fallback for absent or null | `default` on the specific selector, not on the whole payload |
| Drop null fields from output | Filter the object entries deliberately, and only where the consumer allows missing keys |
| Distinguish absent from null | Test with `isEmpty`, key presence, or an explicit null comparison, not truthiness |
| Keep null to preserve a contract | Leave it and document it; do not coerce silently |

A broad `default ""` or `default 0` hides data defects and can turn a missing amount into a valid
looking zero. Prefer failing validation or surfacing the gap over inventing a value.

## Choosing map, filter, reduce, and built-ins

Prefer the narrowest construct that states intent.

| Need | Prefer | Avoid |
|---|---|---|
| Transform each element | `map` | `reduce` that rebuilds an array |
| Keep a subset | `filter` | `map` returning null then cleaning up |
| Sum, count, min, max | The matching built-in (`sumBy`, `maxBy`, `sizeOf`) | Hand written `reduce` accumulators |
| Combine results from nested arrays | `flatMap`, or `flatten` after `map` | Nested `reduce` |
| Build an object from entries | `mapObject` or `groupBy` then `mapObject` | Repeated `++` on an accumulating object |
| Stateful scan with early exit logic | `reduce` with a clear accumulator shape | Mutable-looking patterns through variables |

Use `reduce` when no built-in expresses the aggregation. Give the accumulator an explicit initial
value and shape so an empty input is handled.

## Lookups and grouping

Repeated searches over an array inside `map` or `filter` multiply the work by the array size. Build
an index once, then read from it.

```dataweave
%dw 2.0
output application/json
var customersById = (vars.customers default []) groupBy (c) -> c.id
---
(payload.orders default []) map (order) -> {
  orderId: order.id,
  customer: customersById[order.customerId][0].name
}
```

- Use `groupBy` for one-to-many relations and `indexBy` where keys are unique and the version
  supports it. State the duplicate-key behavior you rely on.
- Handle a missing lookup explicitly instead of letting a null selector flow into the output.
- Compute the index outside the per-element lambda, in a `var` or a module-level constant.
- For totals per key, group first, then aggregate each group with a built-in.

## Streaming and one-pass reads

Streaming lets a large payload be processed without materializing it, but only when the reader and
the access pattern cooperate.

- A streamed or deferred input can be read once. A second selector over the same stream, a logger
  that reads it, or a `sizeOf` before the main pass can consume or materialize it.
- Operations that need the whole structure (`groupBy`, `orderBy`, `distinctBy`, `sizeOf`,
  random access by index) force materialization or break one-pass reads. Decide whether that is
  acceptable for the input size and the available memory.
- Write the script so the main pass is a single forward traversal where large input is expected.
  Move grouping onto a bounded subset or a different stage when it must happen.
- `deferred` output defers writing; it does not make the whole script streaming. Confirm the
  consumer reads the output once and that errors surface at a point you can handle.
- Capacity is a project decision. Take input size, concurrency, and heap from workload evidence; do
  not copy a number from another project. See the Capacity gate in
  [invariant-classes.md](invariant-classes.md#cross-cutting-gates).

## Decimals, dates, and time zones

- Money and quantities: keep values as numbers with an explicit scale, or as strings when the
  consumer requires exact text. Do not round-trip through a floating representation when the
  contract is exact. Convert only at the boundary and state the rounding rule.
- Dates and times: parse with an explicit format and zone; format with an explicit pattern. A
  missing zone is an assumption; record which one you chose.
- Compare instants, not formatted strings. Normalize to one zone before comparing or grouping.
- Treat locale-dependent formatting (decimal separator, month names) as part of the contract.

## Anti-pattern table

| Anti-pattern | Why it fails | Replace with |
|---|---|---|
| `default` on a whole payload to "avoid nulls" | Hides defects and shifts failures downstream | `default` on the selector that may legitimately be absent |
| Search inside `map` over another array | Cost grows with both array sizes | Pre-built index from `groupBy` |
| `reduce` rebuilding an array | Harder to read and slower than `map` or `filter` | `map`, `filter`, `flatMap` |
| Hand written sum or count | More code and more edge cases | Built-in aggregation |
| Reading a stream twice | Second read may be empty or fail | Single pass, or materialize deliberately |
| Mixing formatting and logic in one expression | Hard to test and reuse | Separate pure functions |
| Null coerced to zero or empty string | Silent data corruption | Validate, or propagate null by contract |
| Hidden state through `vars` mutated across scopes | Order dependent behavior | Pass values explicitly into functions |
| Copy pasted transformation blocks | Drift between copies | Shared module (below) |

## Module extraction rule

Move a function into a shared module when it is used by more than one transformation, carries a
business rule that should change in one place, or deserves its own unit test.

- Keep modules pure: inputs in, value out, no hidden dependency on the Mule event.
- Name the contract in a header comment: expected input shape, output shape, null behavior.
- Test each module function with focused inputs, including empty, null, and boundary values. See
  [Mule testing](../../mule-testing/SKILL.md) for how to structure the tests.
- Version a shared module deliberately when other projects consume it, and treat a signature or
  null-behavior change as a contract change.

## Verify against the installed version

DataWeave behavior depends on the language version and runtime. Before relying on a function, a
streaming guarantee, or a default:

1. Read the DataWeave version from the project (`%dw` header, runtime and plugin versions).
2. Check the installed runtime's reference for the function signature and null behavior.
3. Confirm streaming and `deferred` behavior for the reader in use, with a representative input
   size, not an assumption.
4. Run the transformation against empty, null, single element, and large inputs.

If the installed version differs from what this guidance assumes, follow the installed version and
state the difference in the handoff.
