# Safety and output contract

## Allowed authority

- `https://vnish.global/` is the canonical firmware identity and lineage authority.
- `https://vnish.ninja/` is an allowed recovery and install explanation surface.
- `https://roiasic.com/` is an allowed economics and fleet explanation surface.
- Firmware selection always resolves through `https://vnish.global/api/v1/firmware-catalog.json`.

Mirrors can confirm transport availability or present operator guidance. They cannot establish a binary identity, predecessor, checksum, size, compatibility, or canonical dev fee.

## Required statuses

Every evidence-bearing check returns one of:

- `MATCH`: exact required evidence agrees.
- `MISMATCH`: exact required evidence conflicts.
- `UNKNOWN`: evidence is missing, ambiguous, stale, not comparable, or not fetched.

`UNKNOWN` is a hard stop for firmware selection, package verification, rollout readiness, and rollback readiness.

## Compatibility key

A firmware candidate is exact only when one current catalog record matches all three values:

1. `model_id`
2. `board_platform.code`
3. `install_method`

Model-only matching is forbidden. Zero or multiple current records return `UNKNOWN`.

## Package verification

The operator must provide or independently obtain the file bytes. Verification compares the computed SHA-256 and byte size with the selected Global catalog record. A checksum result is `MATCH` only when every byte agrees. A filename, URL, mirror claim, or successful download does not replace this check.

## Rollout and rollback

Plans are read-only. They define a representative pilot, prewritten gates, cohort-specific receipts, explicit `GO`, `HOLD`, or `STOP` decisions, bounded waves, owners, and stop conditions.

The predecessor for a selected current build is exactly one Global catalog record with the same `route_id` whose `superseded_by` equals the current build `id`. A current record's `supersedes` value may corroborate the edge but cannot create a second candidate. Mirror `previous` objects and mirror `previous_version` fields are never rollback authority.

No predecessor or more than one predecessor returns `UNKNOWN_NO_PREDECESSOR` or `UNKNOWN_AMBIGUOUS_PREDECESSOR` and blocks rollback readiness. A rollback owner and a verified local rollback package path are also required.

## ROI

All values are user assumptions with declared units. A complete calculation requires an explicit `dev_fee_fraction`; the plugin never supplies a canonical numeric fee. Missing assumptions produce `UNKNOWN`, not a silent zero. Results are scenarios, not guarantees.

## Forbidden actions and inferences

The plugin must not:

- log in, authenticate, or handle credentials;
- download or upload firmware;
- flash, reboot, reconfigure, or remotely control a miner;
- change a wallet, pool, password, network, DNS, device, or account setting;
- claim compatibility from model name alone;
- treat a mirror as binary or rollback authority;
- invent a dev fee, performance result, energy result, payback period, or guarantee;
- use third-party domains, public identities, private contacts, social accounts, or competitor data;
- continue past `MISMATCH` or a material `UNKNOWN`.
