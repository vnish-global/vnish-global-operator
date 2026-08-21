---
name: miner-compatibility-lookup
description: Determine whether one VNISH firmware catalog record exactly matches a miner using model ID, board platform code, and install method. Use when an operator asks which build applies to a miner or when compatibility evidence must be checked without flashing or changing a device.
---

# Miner compatibility lookup

## Inputs

- Exact `model_id` from the device or verified inventory.
- Exact `board_platform.code` from the device or verified inventory.
- Exact `install_method` required for the device state.
- A current copy of `https://vnish.global/api/v1/firmware-catalog.json`.

## Source priority

The Global catalog is the only compatibility authority. Explanatory pages may help an operator locate device fields, but they cannot select the build.

## Procedure

1. Validate that all three input fields are present and specific.
2. Filter current catalog records by exact `model_id`.
3. Filter the remainder by exact `board_platform.code`.
4. Filter the remainder by exact `install_method`.
5. Require exactly one current record.
6. Return its ID, route ID, filename, byte size, and full SHA-256 as a single immutable candidate.

## Output

Return the three asserted device fields, match count, status, selected record when exact, and a concise reason.

## Hard stops

- Missing any field: `UNKNOWN_MISSING_COMPATIBILITY_FIELD`.
- Zero current matches: `UNKNOWN_NO_EXACT_MATCH`.
- More than one current match: `UNKNOWN_AMBIGUOUS_MATCH`.
- Catalog contradiction or malformed record: `MISMATCH_CATALOG_RECORD`.

## Forbidden inferences

- Model name alone is never enough.
- Do not guess the board code from a product family.
- Do not substitute another install method.
- Do not infer compatibility from filename, mirror availability, or a prior successful flash.
- Do not download or flash anything.

Any unresolved field remains `UNKNOWN` and blocks selection.
