---
name: staged-rollout-rollback
description: Build a read-only VNISH rollout and rollback plan with representative cohorts, prewritten gates, bounded waves, and canonical predecessor resolution. Use when an operator needs a pilot plan, closeout receipts, GO HOLD STOP decisions, or rollback readiness without executing any device action.
---

# Staged rollout and rollback

## Inputs

- The exact current build selected from `https://vnish.global/api/v1/firmware-catalog.json`.
- Verified fleet inventory grouped by model ID, board platform code, install method, and operating context.
- A representative pilot sample.
- User-defined success gates and veto conditions written before results.
- Rollout owner, rollback owner, approved maintenance window, and verified local package paths.

## Source priority

The Global catalog is the only authority for current build identity and predecessor lineage. Fleet inventory, gates, owners, and observation windows must be explicit operator inputs. Mirror route data is never rollback authority.

## Canonical predecessor resolution

1. Let `C` be the selected current Global catalog record.
2. Find Global catalog records with the same `route_id` and `superseded_by == C.id`.
3. Require exactly one record `P`.
4. Treat `C.supersedes == P.id` only as corroboration. A missing or conflicting reciprocal edge is a catalog integrity stop.
5. Verify the local rollback file against `P.size_bytes` and full `P.sha256`.

Never read rollback identity from mirror `previous` objects or mirror `previous_version` fields. They are not rollback authority even when their files and hashes are internally valid.

## Plan structure

1. Freeze the exact current and predecessor identities.
2. Map fleet variation and form visible cohorts.
3. Run a representative pilot under one protocol.
4. Close each cohort separately using one receipt schema.
5. Apply the same prewritten gates and record `GO`, `HOLD`, or `STOP` per cohort.
6. Preserve every valid veto before calculating a fleet summary.
7. Expand only through bounded waves with explicit owners, wave limits, observation windows, and stop conditions.
8. Require a fresh decision before each wave.

## Output

Return a plan only. Include exact build identities, cohort table, pilot definition, evidence fields, gates, vetoes, wave table, owners, observation windows, rollback readiness, and unresolved `UNKNOWN` items.

## Hard stops

- No predecessor: `UNKNOWN_NO_PREDECESSOR`.
- Multiple predecessor candidates: `UNKNOWN_AMBIGUOUS_PREDECESSOR`.
- Reciprocal lineage conflict: `MISMATCH_LINEAGE`.
- Rollback owner or verified rollback package missing: `UNKNOWN_ROLLBACK_NOT_READY`.
- Any cohort veto: `STOP` for the affected scope and no automatic fleet override.
- Any unverified target identity or package: `UNKNOWN` and no wave plan.

## Forbidden inferences

- Do not prewrite an outcome; only gates and vetoes are prewritten.
- Do not let fleet weight erase a valid cohort `STOP`.
- Do not hardcode which routes lack predecessors; resolve the live canonical graph.
- Do not download, flash, reboot, authenticate, or remotely operate miners.
- Do not represent the plan as real telemetry or completed work.

The plan remains `UNKNOWN` wherever exact evidence is not available.
