#!/usr/bin/env python3
"""Fail-closed structural and content validator for this local plugin."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ALLOWED_HOSTS = {"vnish.global", "vnish.ninja", "roiasic.com"}
EXPECTED_SKILLS = {
    "official-source-routing",
    "miner-compatibility-lookup",
    "verify-before-install",
    "staged-rollout-rollback",
    "dev-fee-roi-calculator",
}
FORBIDDEN_TOP_LEVEL = {"commands", "agents", "hooks", "apps", "mcpServers", "settings", "userConfig"}
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt"}
URL_RE = re.compile(r"(?:https?:)?//[^\s`\"'<>]+")
HEX_FRAGMENT_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8,63}(?![0-9A-Fa-f])")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_manifest(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid manifest {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        fail(errors, f"manifest must be an object: {path}")
        return {}
    return value


def validate_url(raw: str, source: Path, errors: list[str]) -> None:
    url = raw.rstrip(".,);]")
    if url.startswith("//"):
        fail(errors, f"protocol-relative URL in {source}: {url}")
        return
    parts = urlsplit(url)
    if parts.scheme != "https":
        fail(errors, f"non-HTTPS URL in {source}: {url}")
    if parts.hostname not in ALLOWED_HOSTS:
        fail(errors, f"unapproved host in {source}: {url}")
    if parts.username or parts.password:
        fail(errors, f"embedded credentials in {source}: {url}")
    try:
        port = parts.port
    except ValueError:
        fail(errors, f"invalid port in {source}: {url}")
        return
    if port not in (None, 443):
        fail(errors, f"non-default port in {source}: {url}")
    host = parts.hostname or ""
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host) or ":" in host:
        fail(errors, f"IP-literal host in {source}: {url}")
    decoded_path = parts.path.lower().replace("%2e", ".")
    if any(piece == ".." for piece in decoded_path.split("/")):
        fail(errors, f"path traversal in {source}: {url}")


def parse_frontmatter(text: str, source: Path, errors: list[str]) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        fail(errors, f"missing YAML frontmatter: {source}")
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(errors, f"unterminated YAML frontmatter: {source}")
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            fail(errors, f"invalid frontmatter line in {source}: {line}")
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        fail(errors, f"frontmatter fields must be name and description only: {source}")
    return fields


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    required_files = {
        ".codex-plugin/plugin.json",
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "README.md",
        "LICENSE",
        "NOTICE",
        "references/source-of-truth-contract.json",
        "references/safety-and-output-contract.md",
        "scripts/roi_calculator.py",
        "scripts/validate_package.py",
        "tests/fixtures/golden-prompts-10-locales.json",
        "tests/test_contract.py",
    }
    actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    for name in sorted(required_files - actual_files):
        fail(errors, f"missing required file: {name}")

    for name in FORBIDDEN_TOP_LEVEL:
        if (root / name).exists():
            fail(errors, f"forbidden component exists: {name}")

    codex = load_manifest(root / ".codex-plugin/plugin.json", errors)
    claude = load_manifest(root / ".claude-plugin/plugin.json", errors)
    marketplace = load_manifest(root / ".claude-plugin/marketplace.json", errors)
    for field in ("name", "version"):
        if codex.get(field) != claude.get(field):
            fail(errors, f"manifest {field} mismatch")
    if codex.get("name") != "vnish-global-operator" or codex.get("version") != "0.1.0":
        fail(errors, "unexpected plugin name or version")
    if codex.get("license") != "Apache-2.0" or claude.get("license") != "Apache-2.0":
        fail(errors, "plugin manifests must use Apache-2.0")
    if codex.get("author") != {"name": "VNISH GLOBAL", "url": "https://vnish.global/"}:
        fail(errors, "Codex publisher identity drift")
    expected_description = (
        "Read-only VNISH firmware routing, compatibility verification, staged rollout planning, "
        "rollback lineage checks, and assumption-led ROI calculation."
    )
    if codex.get("description") != expected_description or claude.get("description") != expected_description:
        fail(errors, "manifest public description drift")
    interface = codex.get("interface")
    if not isinstance(interface, dict):
        fail(errors, "Codex manifest interface must be an object")
    else:
        prompts = interface.get("defaultPrompt")
        if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
            fail(errors, "Codex interface defaultPrompt must be an array of one to three strings")
        elif not all(isinstance(item, str) and item.strip() and len(item) <= 128 for item in prompts):
            fail(errors, "Codex interface defaultPrompt entries must be nonempty strings of at most 128 characters")
        if interface.get("websiteURL") != "https://vnish.global/":
            fail(errors, "Codex website URL drift")
        if interface.get("privacyPolicyURL") != "https://vnish.global/legal/privacy.html":
            fail(errors, "Codex privacy policy URL drift")
        if interface.get("termsOfServiceURL") != "https://vnish.global/legal/terms.html":
            fail(errors, "Codex terms of service URL drift")
    for manifest_name, manifest in (("codex", codex), ("claude", claude)):
        for forbidden in FORBIDDEN_TOP_LEVEL:
            if forbidden in manifest:
                fail(errors, f"{manifest_name} manifest declares forbidden component: {forbidden}")

    if marketplace.get("name") != "vnish-global":
        fail(errors, "unexpected Claude marketplace name")
    owner = marketplace.get("owner")
    if not isinstance(owner, dict) or owner.get("name") != "VNISH GLOBAL" or owner.get("url") != "https://vnish.global/":
        fail(errors, "Claude marketplace owner drift")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1 or not isinstance(plugins[0], dict):
        fail(errors, "Claude marketplace must contain exactly one plugin entry")
    else:
        entry = plugins[0]
        expected_entry = {
            "name": "vnish-global-operator",
            "source": "./",
            "version": "0.1.0",
            "license": "Apache-2.0",
            "strict": True,
        }
        for field, expected in expected_entry.items():
            if entry.get(field) != expected:
                fail(errors, f"Claude marketplace plugin {field} drift")
        if any(field in entry for field in FORBIDDEN_TOP_LEVEL):
            fail(errors, "Claude marketplace entry declares a forbidden component")

    skill_dirs = {path.name for path in (root / "skills").iterdir() if path.is_dir()} if (root / "skills").is_dir() else set()
    if skill_dirs != EXPECTED_SKILLS:
        fail(errors, f"skill inventory mismatch: {sorted(skill_dirs)}")
    for name in sorted(EXPECTED_SKILLS):
        source = root / "skills" / name / "SKILL.md"
        if not source.is_file():
            fail(errors, f"missing skill file: {source.relative_to(root)}")
            continue
        text = source.read_text(encoding="utf-8")
        fields = parse_frontmatter(text, source, errors)
        if fields.get("name") != name:
            fail(errors, f"skill directory and name differ: {source}")
        for required_phrase in ("## Inputs", "## Source priority", "## Output", "## Hard stops", "## Forbidden inferences", "UNKNOWN"):
            if required_phrase not in text:
                fail(errors, f"missing required skill contract phrase {required_phrase!r}: {source}")

    text_files = [path for path in root.rglob("*") if path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name == "LICENSE")]
    for source in text_files:
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(errors, f"non-UTF-8 text file: {source}")
            continue
        if chr(0x2013) in text or chr(0x2014) in text:
            fail(errors, f"long dash found: {source}")
        relative = source.relative_to(root).as_posix()
        url_scoped = (
            relative.startswith(".codex-plugin/")
            or relative.startswith(".claude-plugin/")
            or relative.startswith("skills/")
            or relative.startswith("references/")
            or relative == "README.md"
        )
        if url_scoped:
            for raw in URL_RE.findall(text):
                validate_url(raw, source, errors)

        if relative.startswith("skills/") or relative == "README.md":
            if HEX_FRAGMENT_RE.search(text):
                fail(errors, f"truncated hash-like fragment in public instruction: {source}")
            lowered = text.lower()
            for marker in ("mailto:", "tel:", "@gmail.", "@outlook.", "twitter.com/", "x.com/", "linkedin.com/", "t.me/"):
                if marker in lowered:
                    fail(errors, f"contact or social marker in public instruction: {source}")

    try:
        contract = json.loads((root / "references/source-of-truth-contract.json").read_text(encoding="utf-8"))
        policy = contract["network_policy"]
        if set(policy["allowed_hosts"]) != ALLOWED_HOSTS or policy["allowed_schemes"] != ["https"]:
            fail(errors, "source-of-truth contract network allowlist drift")
        registry = contract["source_registry"]
        catalog = next(item for item in registry if item.get("id") == "global_catalog")
        if catalog.get("url") != "https://vnish.global/api/v1/firmware-catalog.json":
            fail(errors, "Global catalog URL drift")
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
        fail(errors, f"invalid source-of-truth contract: {exc}")

    try:
        golden = json.loads(
            (root / "tests/fixtures/golden-prompts-10-locales.json").read_text(encoding="utf-8")
        )
        expected_locales = {"en", "es", "pt-BR", "de", "fr", "zh-CN", "ar", "ja", "ko", "ru"}
        if set(golden.get("locales", {})) != expected_locales:
            fail(errors, "golden prompt locale inventory mismatch")
        for locale, panel in golden.get("locales", {}).items():
            if not isinstance(panel, dict):
                fail(errors, f"golden prompt panel must be an object: {locale}")
                continue
            if len(panel.get("positive", [])) != 5 or len(panel.get("negative", [])) != 3:
                fail(errors, f"golden prompt counts must be 5 positive and 3 negative: {locale}")
            for case in panel.get("positive", []) + panel.get("negative", []):
                if not isinstance(case, dict):
                    fail(errors, f"golden prompt case must be an object: {locale}")
                    continue
                if case.get("expected_skill") not in EXPECTED_SKILLS:
                    fail(errors, f"golden prompt has unknown skill: {locale}")
                if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
                    fail(errors, f"golden prompt text is missing: {locale}")
                if not isinstance(case.get("expected_behavior"), str) or not case["expected_behavior"].strip():
                    fail(errors, f"golden expected behavior is missing: {locale}")
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        fail(errors, f"invalid golden prompt panel: {exc}")

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS")
    print(f"plugin_root={root}")
    print(f"skills={len(EXPECTED_SKILLS)}")
    print(f"allowed_hosts={','.join(sorted(ALLOWED_HOSTS))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
