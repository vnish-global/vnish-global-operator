---
name: dev-fee-roi-calculator
description: Calculate a transparent VNISH fleet economics scenario from explicit user assumptions, including an explicit dev fee fraction, energy cost, hashprice, duty cycle, and other costs. Use when an operator asks for ROI, net revenue, incremental economics, sensitivity, or payback without treating any number as canonical or guaranteed.
---

# Dev fee ROI calculator

## Inputs

Provide explicit numeric user assumptions with units for:

- fleet size;
- baseline and candidate hashrate in TH/s;
- baseline and candidate power in watts;
- electricity price per kWh;
- hashprice per TH/day;
- duty cycle as a fraction;
- dev fee as a fraction;
- other operating cost per unit/day;
- one-time fleet cost.

Optional sensitivity multipliers must also come from the user.

## Source priority

This calculation uses only stated user assumptions. Public domains can explain the method but do not supply a canonical numeric dev fee or guarantee a result.

## Formula

For each unit:

- gross daily revenue = hashrate * hashprice
- daily energy cost = watts / 1000 * 24 * duty cycle * electricity price
- daily dev fee cost = gross daily revenue * dev fee fraction
- net daily value = gross daily revenue - energy cost - dev fee cost - other operating cost

Multiply unit values by fleet size. Incremental value is candidate minus baseline. Payback is one-time fleet cost divided by positive incremental daily fleet value only.

## Output

Return:

- `status`: `MATCH` for a complete internally consistent scenario, otherwise `UNKNOWN`;
- every assumption with unit and `USER_ASSUMPTION` provenance;
- the formulas used;
- baseline, candidate, and delta values;
- payback only when incremental daily value is positive;
- sensitivity results only for explicit user multipliers;
- unknown fields and a no-guarantee note.

## Hard stops

- Missing dev fee fraction: `UNKNOWN_MISSING_DEV_FEE`.
- Missing required assumption: `UNKNOWN_MISSING_ASSUMPTION`.
- Invalid, negative, non-finite, or out-of-range value: `UNKNOWN_INVALID_ASSUMPTION`.
- Nonpositive incremental daily value: no payback calculation.

## Forbidden inferences

- Do not invent or publish a canonical numeric dev fee.
- Do not silently substitute zero for a missing value.
- Do not claim measured performance, savings, profitability, or guaranteed payback.
- Do not fetch prices or device metrics unless the user separately supplies and authorizes those exact inputs.

Unresolved inputs remain `UNKNOWN` and must be shown to the user.
