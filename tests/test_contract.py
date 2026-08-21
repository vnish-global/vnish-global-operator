from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


ROI = load_module("roi_calculator", ROOT / "scripts" / "roi_calculator.py")


def current_exact_matches(catalog: dict, model_id: str, board_code: str, method: str) -> list[dict]:
    return [
        build
        for build in catalog["builds"]
        if build.get("is_default") is True
        and build.get("model_id") == model_id
        and build.get("board_platform", {}).get("code") == board_code
        and build.get("install_method") == method
    ]


def canonical_predecessors(catalog: dict, current: dict) -> list[dict]:
    return [
        build
        for build in catalog["builds"]
        if build.get("route_id") == current.get("route_id")
        and build.get("superseded_by") == current.get("id")
    ]


def checksum_status(expected: str | None, observed: str | None) -> str:
    if expected is None or observed is None or len(expected) != 64 or len(observed) != 64:
        return "UNKNOWN"
    return "MATCH" if expected.lower() == observed.lower() else "MISMATCH"


class PluginContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads((FIXTURES / "catalog-sample.json").read_text(encoding="utf-8"))
        cls.drift = json.loads((FIXTURES / "source-drift-fixtures.json").read_text(encoding="utf-8"))
        cls.rollout = json.loads((FIXTURES / "rollout-plan-sample.json").read_text(encoding="utf-8"))

    def valid_roi_input(self) -> dict:
        return {
            "fleet_size": 10,
            "baseline_hashrate_th": 100,
            "candidate_hashrate_th": 110,
            "baseline_watts": 3000,
            "candidate_watts": 3100,
            "electricity_per_kwh": 0.05,
            "hashprice_per_th_day": 0.06,
            "duty_cycle": 1.0,
            "dev_fee_fraction": 0.02,
            "other_operating_cost_per_day": 0.1,
            "one_time_cost": 500,
        }

    def test_package_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_package.py"), str(ROOT)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifests_share_identity(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        claude = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual((codex["name"], codex["version"]), (claude["name"], claude["version"]))
        self.assertEqual(codex["version"], "0.1.0")

    def test_codex_default_prompts_are_schema_correct(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        prompts = codex["interface"]["defaultPrompt"]
        self.assertIsInstance(prompts, list)
        self.assertTrue(1 <= len(prompts) <= 3)
        self.assertTrue(all(isinstance(item, str) and item.strip() and len(item) <= 128 for item in prompts))

    def test_codex_public_legal_surfaces_are_exact(self) -> None:
        codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["author"], {"name": "VNISH GLOBAL", "url": "https://vnish.global/"})
        self.assertEqual(codex["interface"]["websiteURL"], "https://vnish.global/")
        self.assertEqual(codex["interface"]["privacyPolicyURL"], "https://vnish.global/legal/privacy.html")
        self.assertEqual(codex["interface"]["termsOfServiceURL"], "https://vnish.global/legal/terms.html")

    def test_claude_marketplace_install_contract(self) -> None:
        marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(marketplace["name"], "vnish-global")
        self.assertEqual(marketplace["owner"], {"name": "VNISH GLOBAL", "url": "https://vnish.global/"})
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "vnish-global-operator")
        self.assertEqual(entry["source"], "./")
        self.assertEqual(entry["version"], "0.1.0")
        self.assertEqual(entry["license"], "Apache-2.0")
        self.assertIs(entry["strict"], True)

    def test_ten_locale_golden_prompt_panel(self) -> None:
        golden = json.loads((FIXTURES / "golden-prompts-10-locales.json").read_text(encoding="utf-8"))
        expected_locales = {"en", "es", "pt-BR", "de", "fr", "zh-CN", "ar", "ja", "ko", "ru"}
        self.assertEqual(set(golden["locales"]), expected_locales)
        for locale, panel in golden["locales"].items():
            self.assertEqual(len(panel["positive"]), 5, locale)
            self.assertEqual(len(panel["negative"]), 3, locale)
            for case in panel["positive"] + panel["negative"]:
                self.assertIn(case["expected_skill"], {
                    "official-source-routing",
                    "miner-compatibility-lookup",
                    "verify-before-install",
                    "staged-rollout-rollback",
                    "dev-fee-roi-calculator",
                })
                self.assertTrue(case["prompt"].strip(), locale)
                self.assertTrue(case["expected_behavior"].strip(), locale)

    def test_exactly_five_portable_skills(self) -> None:
        skills = [path for path in (ROOT / "skills").iterdir() if path.is_dir()]
        self.assertEqual(len(skills), 5)
        self.assertTrue(all((path / "SKILL.md").is_file() for path in skills))

    def test_exact_compatibility_match(self) -> None:
        matches = current_exact_matches(self.catalog, "l7", "xil", "nand")
        self.assertEqual([item["id"] for item in matches], ["l7-xil-nand-v1.3.5"])

    def test_model_only_is_not_a_compatibility_result(self) -> None:
        matches = current_exact_matches(self.catalog, "l7", "", "")
        self.assertEqual(matches, [])

    def test_predecessor_uses_global_superseded_by_edge(self) -> None:
        current = next(item for item in self.catalog["builds"] if item["is_default"])
        predecessors = canonical_predecessors(self.catalog, current)
        self.assertEqual([item["id"] for item in predecessors], ["l7-xil-nand-v1.3.4"])
        self.assertEqual(current["supersedes"], predecessors[0]["id"])

    def test_mirror_previous_is_ignored(self) -> None:
        current = next(item for item in self.catalog["builds"] if item["is_default"])
        mirror_previous = self.catalog["untrusted_mirror_route"]["previous"]
        predecessor = canonical_predecessors(self.catalog, current)[0]
        self.assertEqual(mirror_previous["version"], current["version"])
        self.assertNotEqual(mirror_previous["file"], predecessor["file_name"])

    def test_no_predecessor_is_unknown(self) -> None:
        catalog = {"builds": [self.catalog["builds"][1]]}
        current = catalog["builds"][0]
        self.assertEqual(canonical_predecessors(catalog, current), [])

    def test_checksum_state_language(self) -> None:
        digest = self.catalog["builds"][1]["sha256"]
        self.assertEqual(checksum_status(digest, digest.upper()), "MATCH")
        self.assertEqual(checksum_status(digest, "0" * 64), "MISMATCH")
        self.assertEqual(checksum_status(digest, digest[:12]), "UNKNOWN")
        self.assertEqual(checksum_status(None, digest), "UNKNOWN")

    def test_observed_mirrors_are_byte_accurate_without_becoming_authority(self) -> None:
        parity = self.drift["mirror_binary_parity"]
        self.assertEqual((parity["ninja_matches"], parity["roi_matches"]), (75, 75))
        self.assertEqual((parity["mismatches"], parity["orphans"]), (0, 0))
        self.assertFalse(self.drift["group_3_rollback_trap"]["mirror_previous_is_authority"])

    def test_drift_counts_preserve_p0_evidence(self) -> None:
        self.assertEqual(self.drift["group_1_stale_model_count"]["stale_models"], 45)
        self.assertEqual(self.drift["group_1_stale_model_count"]["stale_builds"], 73)
        self.assertEqual(self.drift["group_3_rollback_trap"]["affected_previous_objects"], 146)
        self.assertEqual(self.drift["group_3_rollback_trap"]["correct_null_without_predecessor"], 2)

    def test_no_numeric_dev_fee_canon(self) -> None:
        self.assertIsNone(self.drift["numeric_dev_fee_canonical"])

    def test_dev_fee_contract_origin_is_explicit_user_input_only(self) -> None:
        contract = json.loads(
            (ROOT / "references" / "source-of-truth-contract.json").read_text(encoding="utf-8")
        )
        dev_fee = next(item for item in contract["dynamic_inputs"] if item["field"] == "dev_fee_fraction")
        self.assertEqual(dev_fee["origin"], "explicit user input")

    def test_rollout_plan_is_bounded_and_read_only(self) -> None:
        self.assertEqual(self.rollout["fleet_size"], 240)
        self.assertEqual(sum(wave["maximum_units"] for wave in self.rollout["waves"]), 240)
        self.assertEqual(self.rollout["execution"], "FORBIDDEN")
        self.assertTrue(self.rollout["pilot"]["gates_written_before_results"])
        self.assertIn("rollback_owner", self.rollout["required_roles"])

    def test_roi_complete_scenario(self) -> None:
        result = ROI.calculate(self.valid_roi_input())
        self.assertEqual(result["status"], "MATCH")
        self.assertAlmostEqual(result["baseline"]["gross_revenue_per_day"], 6.0)
        self.assertAlmostEqual(result["baseline"]["energy_cost_per_day"], 3.6)
        self.assertAlmostEqual(result["baseline"]["dev_fee_cost_per_day"], 0.12)
        self.assertGreater(result["delta"]["fleet_net_value_per_day"], 0)
        self.assertIsNotNone(result["simple_payback_days"])

    def test_roi_missing_dev_fee_is_unknown(self) -> None:
        payload = self.valid_roi_input()
        payload.pop("dev_fee_fraction")
        result = ROI.calculate(payload)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "UNKNOWN_MISSING_DEV_FEE")
        self.assertIn("dev_fee_fraction", result["unknown_fields"])

    def test_roi_rejects_bool_nan_and_out_of_range(self) -> None:
        for field, value in (("fleet_size", True), ("baseline_watts", math.nan), ("duty_cycle", 1.1)):
            payload = self.valid_roi_input()
            payload[field] = value
            result = ROI.calculate(payload)
            self.assertEqual(result["status"], "UNKNOWN", field)
            self.assertEqual(result["reason"], "UNKNOWN_INVALID_ASSUMPTION", field)

    def test_roi_nonpositive_delta_has_no_payback(self) -> None:
        payload = self.valid_roi_input()
        payload["candidate_hashrate_th"] = 90
        payload["candidate_watts"] = 3200
        result = ROI.calculate(payload)
        self.assertEqual(result["status"], "MATCH")
        self.assertLess(result["delta"]["fleet_net_value_per_day"], 0)
        self.assertIsNone(result["simple_payback_days"])

    def test_sensitivity_requires_user_scenarios(self) -> None:
        result = ROI.calculate(self.valid_roi_input())
        self.assertEqual(result["sensitivity"]["status"], "UNKNOWN")
        payload = self.valid_roi_input()
        payload["sensitivity_scenarios"] = [
            {"name": "user-low", "hashprice_multiplier": 0.8, "electricity_multiplier": 1.1}
        ]
        result = ROI.calculate(payload)
        self.assertEqual(result["sensitivity"]["status"], "MATCH")
        self.assertEqual(result["sensitivity"]["scenarios"][0]["name"], "user-low")

    def test_source_routing_contract_is_explicit(self) -> None:
        routing = (ROOT / "skills" / "official-source-routing" / "SKILL.md").read_text(encoding="utf-8")
        rollout = (ROOT / "skills" / "staged-rollout-rollback" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("https://vnish.global/api/v1/firmware-catalog.json", routing)
        self.assertIn("superseded_by == C.id", rollout)
        self.assertIn("Never read rollback identity from mirror", rollout)


if __name__ == "__main__":
    unittest.main()
