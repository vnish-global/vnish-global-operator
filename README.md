# VNISH Global Operator

[简体中文说明](README.zh-CN.md)

Version `0.1.0` is a read-only, skills-only plugin for five bounded tasks:

1. Route a VNISH question to an allowed first-party source.
2. Match a miner only when model, board platform, and install method are exact.
3. Verify a package identity before an operator-controlled install.
4. Produce a staged rollout and rollback plan without touching a device.
5. Calculate transparent ROI scenarios from explicit user assumptions.

## Authority boundary

Firmware identity and lineage come only from the catalog at `https://vnish.global/api/v1/firmware-catalog.json`. The other allowed first-party surfaces can explain recovery or economics, but they do not select a binary and cannot override catalog identity.

The plugin never logs in, downloads firmware, flashes a miner, changes credentials, changes network settings, starts a rollout, or performs a rollback. It returns `UNKNOWN` and stops whenever exact evidence is missing, contradictory, stale, or ambiguous.

## Validation

Run the package validator and test suite before review:

```text
python3 scripts/validate_package.py .
python3 -m unittest discover -s tests -v
```

The included ROI calculator reads JSON from standard input or from `--input`. It never invents a dev fee. `dev_fee_fraction` is a required user assumption for a complete result.

The golden prompt panel covers English, Spanish, Brazilian Portuguese, German, French, Simplified Chinese, Arabic, Japanese, Korean, and Russian. Every locale contains five positive routing cases and three negative hard-stop cases. All locales exercise the same canonical technical contract rather than maintaining translated copies of firmware facts.

## Install in Claude Code

Add the public VNISH GLOBAL marketplace and install the plugin:

```text
claude plugin marketplace add vnish-global/vnish-global-operator
claude plugin install vnish-global-operator@vnish-global
```

The marketplace and plugin remain read-only. Installation adds instructions and local calculation helpers only. It does not download firmware, contact miners, request credentials, or change device or account state.

## Safety and public surfaces

This plugin contains no commands, agents, hooks, apps, MCP servers, credentials, or device actions. It does not change any device, public account, or external system.

The first-party privacy policy is at `https://vnish.global/legal/privacy.html`, the terms of service are at `https://vnish.global/legal/terms.html`, and the public product and support entry surface is `https://vnish.global/`.

## License boundary

Apache License 2.0 applies only to the plugin files published in this repository. It does not license VNISH firmware binaries, closed or private source code, internal repositories, credentials, brand artwork, logos, trade names, service marks, or trademarks. Section 6 of the Apache License 2.0 preserves the trademark boundary. See `NOTICE`.
