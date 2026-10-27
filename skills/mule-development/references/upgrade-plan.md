# Runtime and Java upgrade plan

Use this reference when a Mule 4 application moves to a newer runtime version, a newer Java
version, or both. It does not cover Mule 3 to Mule 4 migration. It applies the version, Class A,
Class D, and validation gates from
[Invariant classes and cross-cutting gates](invariant-classes.md) to a change whose blast radius is
the whole application.

## Contents

1. [Baseline before changing anything](#baseline-before-changing-anything)
2. [Validate the target pair](#validate-the-target-pair)
3. [Impact inventory](#impact-inventory)
4. [Present the plan and wait](#present-the-plan-and-wait)
5. [Execute in order](#execute-in-order)
6. [Classify failures and stop on repeats](#classify-failures-and-stop-on-repeats)
7. [Rollback and rollout](#rollback-and-rollout)

## Baseline before changing anything

Build and run the full test suite on the current runtime and current JDK first, and record the
result: test count, failures, warnings, and the JDK the build reported. A failure that exists
before the upgrade is not an upgrade regression, and without a baseline every later failure is
ambiguous. If the suite cannot run at baseline, fix or record that first through `mule-testing`;
do not start the upgrade on an unproven toolchain.

## Validate the target pair

Treat the runtime and Java version as one target pair. Look up the pair's support, and every
connector's and plugin's support for it, through
[`mule-dependencies`](../../mule-dependencies/SKILL.md) with a live lookup, not memory. Record the
versions found and where the answer came from. Run the mule-build compatibility check against the
target pair when the server provides it; an inconclusive result is not a pass.

## Impact inventory

Build the inventory from the project, not from a generic list. Each item is a check to run
against the code; change code only where the check finds a use.

| Area | Check |
| --- | --- |
| Connectors and plugins | List each one whose supported Java or minimum runtime excludes the target, and the first version that includes it |
| Operations and error types | For each connector bump, read the release notes across the actual version span (installed to target) for removed or renamed operations, changed defaults, and changed error types; then search the project for each one. Never rely on remembered changes |
| Error handling | Every `type=` in error handlers and `until-successful` scopes still names an error the new connector version raises |
| DataWeave on a newer JDK | Search for the behaviors below and verify each use with a fixture |
| MUnit | Mock and assertion shape changes across the MUnit span, and one MUnit version for plugin, runner, and tools (see `mule-testing`) |
| Build | Maven plugin, enforcer rules, and toolchain settings that pin the old JDK |

DataWeave and Java behavior points to verify where the project uses them:

- Number coercion from formatted strings (grouping separators, decimal marks, exponents).
- Date and number formatting or parsing that relies on the default locale, including month and
  day names.
- The default charset where a read or write does not name an encoding.
- Scripting engines removed from newer JDKs, used through a scripting module or Java call.
- Access to internal JDK classes through `java!` or Java module calls, which strong encapsulation
  can block.
- Three-letter time zone identifiers, which are ambiguous; prefer region identifiers where the
  project parses or formats zones.

## Present the plan and wait

State the plan in the reply: the target pair and its evidence, the version pins to change, the
inventory findings with the code each one touches, the validation, and the rollback note. Wait for
the user's approval before editing. Keep the plan in the conversation, not in a file in the
project.

## Execute in order

1. Change version pins only: runtime, Java target, connectors, plugins, and MUnit.
2. Confirm the pins resolved: read the resolved dependency tree from a mule-build build or the
   project's Maven command and check every changed artifact appears at the intended version, with
   no conflicting older copy.
3. Build and run the baseline suite on the target JDK before editing source, so failures caused by
   the pins alone are visible.
4. Edit source only for inventory findings and failures traced to the upgrade.
5. Rerun the full suite and package, then complete the
   [Post-Development Checklist](post-development-checklist.md).

## Classify failures and stop on repeats

Classify each failure before editing: resolution or toolchain, compile or schema, connector
operation or error-type change, DataWeave behavior change, MUnit shape change, or a defect that
also fails at baseline. Fix one class at a time and rerun. When the same failure returns after a
fix, stop and report the evidence instead of trying variations; a repeat means the diagnosis is
wrong.

## Rollback and rollout

Keep a rollback note before the first deploy: the currently running artifact by full name and
digest, the runtime version it runs on, and whether returning to it needs any property or runtime
change. Hand the rollout to
[the release lifecycle](../../mule-ops/references/release-lifecycle.md) and
[safe change](../../mule-ops/references/safe-change.md); a runtime change is a full start and
follows the same checks as any release.
