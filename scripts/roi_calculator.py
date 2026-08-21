#!/usr/bin/env python3
"""Pure offline ROI scenario calculator for explicit user assumptions."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


REQUIRED = {
    "fleet_size": "units",
    "baseline_hashrate_th": "TH/s per unit",
    "candidate_hashrate_th": "TH/s per unit",
    "baseline_watts": "W per unit",
    "candidate_watts": "W per unit",
    "electricity_per_kwh": "currency/kWh",
    "hashprice_per_th_day": "currency/TH/day",
    "duty_cycle": "fraction",
    "dev_fee_fraction": "fraction",
    "other_operating_cost_per_day": "currency/unit/day",
    "one_time_cost": "currency/fleet",
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _validate(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    missing = [name for name in REQUIRED if name not in payload]
    errors: list[str] = []

    for name in REQUIRED:
        if name not in payload:
            continue
        value = payload[name]
        if not _is_number(value):
            errors.append(f"{name} must be a finite number")
            continue
        if value < 0:
            errors.append(f"{name} must not be negative")

    fleet_size = payload.get("fleet_size")
    if _is_number(fleet_size) and (fleet_size <= 0 or int(fleet_size) != fleet_size):
        errors.append("fleet_size must be a positive integer")

    for name in ("duty_cycle", "dev_fee_fraction"):
        value = payload.get(name)
        if _is_number(value) and not 0 <= value <= 1:
            errors.append(f"{name} must be between 0 and 1")

    sensitivity = payload.get("sensitivity_scenarios")
    if sensitivity is not None:
        if not isinstance(sensitivity, list):
            errors.append("sensitivity_scenarios must be a list")
        else:
            for index, scenario in enumerate(sensitivity):
                if not isinstance(scenario, dict):
                    errors.append(f"sensitivity_scenarios[{index}] must be an object")
                    continue
                for name in ("hashprice_multiplier", "electricity_multiplier"):
                    value = scenario.get(name)
                    if not _is_number(value) or value < 0:
                        errors.append(f"sensitivity_scenarios[{index}].{name} must be finite and nonnegative")

    return missing, errors


def _unit_case(
    hashrate_th: float,
    watts: float,
    electricity_per_kwh: float,
    hashprice_per_th_day: float,
    duty_cycle: float,
    dev_fee_fraction: float,
    other_cost: float,
) -> dict[str, float]:
    gross = hashrate_th * hashprice_per_th_day
    energy = watts / 1000 * 24 * duty_cycle * electricity_per_kwh
    fee = gross * dev_fee_fraction
    net = gross - energy - fee - other_cost
    return {
        "gross_revenue_per_day": gross,
        "energy_cost_per_day": energy,
        "dev_fee_cost_per_day": fee,
        "other_operating_cost_per_day": other_cost,
        "net_value_per_day": net,
    }


def _round_tree(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, dict):
        return {key: _round_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_tree(item) for item in value]
    return value


def calculate(payload: dict[str, Any]) -> dict[str, Any]:
    missing, errors = _validate(payload)
    if missing or errors:
        return {
            "status": "UNKNOWN",
            "reason": "UNKNOWN_MISSING_DEV_FEE"
            if "dev_fee_fraction" in missing
            else "UNKNOWN_MISSING_ASSUMPTION"
            if missing
            else "UNKNOWN_INVALID_ASSUMPTION",
            "unknown_fields": missing,
            "errors": errors,
            "note": "No missing or invalid assumption was replaced with a default. This is not a guarantee.",
        }

    inputs = {name: float(payload[name]) for name in REQUIRED}
    fleet_size = int(inputs["fleet_size"])

    baseline = _unit_case(
        inputs["baseline_hashrate_th"],
        inputs["baseline_watts"],
        inputs["electricity_per_kwh"],
        inputs["hashprice_per_th_day"],
        inputs["duty_cycle"],
        inputs["dev_fee_fraction"],
        inputs["other_operating_cost_per_day"],
    )
    candidate = _unit_case(
        inputs["candidate_hashrate_th"],
        inputs["candidate_watts"],
        inputs["electricity_per_kwh"],
        inputs["hashprice_per_th_day"],
        inputs["duty_cycle"],
        inputs["dev_fee_fraction"],
        inputs["other_operating_cost_per_day"],
    )

    baseline["fleet_net_value_per_day"] = baseline["net_value_per_day"] * fleet_size
    candidate["fleet_net_value_per_day"] = candidate["net_value_per_day"] * fleet_size
    delta = {
        key: candidate[key] - baseline[key]
        for key in (
            "gross_revenue_per_day",
            "energy_cost_per_day",
            "dev_fee_cost_per_day",
            "net_value_per_day",
            "fleet_net_value_per_day",
        )
    }
    incremental = delta["fleet_net_value_per_day"]
    payback = inputs["one_time_cost"] / incremental if incremental > 0 else None

    sensitivity_input = payload.get("sensitivity_scenarios")
    sensitivity: dict[str, Any]
    if sensitivity_input is None:
        sensitivity = {
            "status": "UNKNOWN",
            "reason": "UNKNOWN_NO_USER_SENSITIVITY_SCENARIOS",
            "scenarios": [],
        }
    else:
        scenarios = []
        for index, item in enumerate(sensitivity_input):
            hashprice = inputs["hashprice_per_th_day"] * float(item["hashprice_multiplier"])
            electricity = inputs["electricity_per_kwh"] * float(item["electricity_multiplier"])
            base_case = _unit_case(
                inputs["baseline_hashrate_th"],
                inputs["baseline_watts"],
                electricity,
                hashprice,
                inputs["duty_cycle"],
                inputs["dev_fee_fraction"],
                inputs["other_operating_cost_per_day"],
            )
            candidate_case = _unit_case(
                inputs["candidate_hashrate_th"],
                inputs["candidate_watts"],
                electricity,
                hashprice,
                inputs["duty_cycle"],
                inputs["dev_fee_fraction"],
                inputs["other_operating_cost_per_day"],
            )
            scenarios.append(
                {
                    "name": item.get("name", f"scenario-{index + 1}"),
                    "hashprice_multiplier": item["hashprice_multiplier"],
                    "electricity_multiplier": item["electricity_multiplier"],
                    "incremental_fleet_net_value_per_day":
                    (candidate_case["net_value_per_day"] - base_case["net_value_per_day"]) * fleet_size,
                }
            )
        sensitivity = {"status": "MATCH", "scenarios": scenarios}

    assumptions = {
        name: {
            "value": payload[name],
            "unit": unit,
            "provenance": "USER_ASSUMPTION",
        }
        for name, unit in REQUIRED.items()
    }

    return _round_tree(
        {
            "status": "MATCH",
            "assumptions": assumptions,
            "formulas": {
                "gross_revenue_per_day": "hashrate_th * hashprice_per_th_day",
                "energy_cost_per_day": "watts / 1000 * 24 * duty_cycle * electricity_per_kwh",
                "dev_fee_cost_per_day": "gross_revenue_per_day * dev_fee_fraction",
                "net_value_per_day": "gross_revenue_per_day - energy_cost_per_day - dev_fee_cost_per_day - other_operating_cost_per_day",
                "fleet_net_value_per_day": "net_value_per_day * fleet_size",
                "incremental_fleet_net_value_per_day": "candidate - baseline",
                "simple_payback_days": "one_time_cost / positive incremental_fleet_net_value_per_day",
            },
            "baseline": baseline,
            "candidate": candidate,
            "delta": delta,
            "simple_payback_days": payback,
            "payback_note": "Not calculated because incremental daily fleet value is not positive."
            if payback is None
            else "Scenario output from user assumptions only.",
            "sensitivity": sensitivity,
            "unknown_fields": [],
            "note": "Scenario only. Inputs are user assumptions, not measured results or a guarantee.",
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Read input JSON from a local file instead of stdin")
    args = parser.parse_args()

    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        result = calculate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "status": "UNKNOWN",
            "reason": "UNKNOWN_INVALID_INPUT",
            "unknown_fields": [],
            "errors": [str(exc)],
            "note": "No calculation was performed. This is not a guarantee.",
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
