---
name: verify-before-install
description: Verify a locally available VNISH package against one exact Global catalog record before an operator-controlled install. Use when file identity, byte size, SHA-256, source route, or pre-install safety evidence must be checked without downloading, uploading, or flashing firmware.
---

# Verify before install

## Inputs

- The exact selected Global catalog record.
- A local file path supplied by the operator.
- The previously verified compatibility tuple: `model_id`, `board_platform.code`, and `install_method`.

## Source priority

Expected filename, size, checksum, route, and compatibility come only from `https://vnish.global/api/v1/firmware-catalog.json`.

## Procedure

1. Confirm the selected record is still the unique current exact compatibility match.
2. Confirm the local path exists and resolves to a regular file.
3. Compute its byte size and SHA-256 locally.
4. Compare full values with the selected record.
5. Keep compatibility, size, and checksum as separate evidence rows.

## Output

Return an evidence table containing expected value, observed value, source, and `MATCH`, `MISMATCH`, or `UNKNOWN` for each check. End with `READY_FOR_OPERATOR_REVIEW` only if every required row is `MATCH`.

## Hard stops

- Missing or unreadable file: `UNKNOWN_LOCAL_FILE`.
- Compatibility not exact: `UNKNOWN_COMPATIBILITY` or `MISMATCH_COMPATIBILITY`.
- Size differs: `MISMATCH_SIZE`.
- Any checksum byte differs: `MISMATCH_SHA256`.
- Catalog changed after selection: `UNKNOWN_STALE_SELECTION`.

## Forbidden inferences

- Filename equality does not prove file identity.
- A mirror URL or successful transfer does not prove file identity.
- A partial or shortened hash is not comparable.
- Never download, upload, install, flash, reboot, or change a device.

Missing evidence stays `UNKNOWN`; it is never treated as `MATCH`.
