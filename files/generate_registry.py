#!/usr/bin/env python3
# Reads all per-example result files produced by run_example.py,
# computes each example's health, and writes one JSON file per example
# into the registry directory.
#
# Only writes a registry file if something meaningful changed — this keeps
# git diffs clean and avoids noisy "just a date bump" commits.
#
# Usage:
#   python scripts/generate_registry.py \
#       --results-dir results/ \
#       --registry-dir registry/ \
#       --examples-dir examples/

import argparse
import json
from datetime import date
from pathlib import Path

import yaml  # pip install pyyaml

# ---------------------------------------------------------------------------
# Frontmatter parser (identical to the one in run_example.py)
# ---------------------------------------------------------------------------


def parse_frontmatter(readme_path: Path) -> dict:
    if not readme_path.exists():
        return {}
    text = readme_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    close = text.find("\n---", 3)
    if close == -1:
        return {}
    try:
        return yaml.safe_load(text[3:close]) or {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------------------
# Health computation
# ---------------------------------------------------------------------------


def compute_health(results_by_version: dict) -> tuple:
    """
    Apply the health rules in the exact order specified:

      1. stable fails               → broken
      2. stable passes, main fails  → warning
      3. any run produced a warning → warning
      4. otherwise                  → passing

    Returns (health_string, first_warning_string_or_None).
    """
    stable = results_by_version.get("stable")
    main = results_by_version.get("main")

    # Pick up the first non-null warning across any tested version.
    first_warn = None
    for vr in results_by_version.values():
        if vr and vr.get("warning"):
            first_warn = vr["warning"]
            break

    # No stable result at all (example was never run, or only main was run).
    if stable is None:
        return "untested", None

    # ci.skip = true in the frontmatter → explicitly untested.
    if stable.get("skipped"):
        return "untested", None

    stable_passed = stable.get("passed", False)

    if not stable_passed:
        return "broken", first_warn

    # main can be absent (not tested yet), skipped, or have a result.
    main_tested = main is not None and not main.get("skipped")
    if main_tested and not main.get("passed", True):
        return "warning", first_warn

    if first_warn:
        return "warning", first_warn

    return "passing", None


# ---------------------------------------------------------------------------
# Result file loader
# ---------------------------------------------------------------------------


def load_results(results_dir: Path) -> dict:
    """
    Read every *.json file in results_dir and group them as:
        { example_id: { version_label: result_dict, ... }, ... }

    Expected filename pattern: <example_id>_<version>.json
    """
    grouped: dict = {}
    for f in results_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ex_id = data.get("example_id")
        version = data.get("version")
        if ex_id and version:
            grouped.setdefault(ex_id, {})[version] = data
    return grouped


# ---------------------------------------------------------------------------
# Registry record builder
# ---------------------------------------------------------------------------


def build_record(example_id: str, example_path: Path, results: dict) -> dict:
    """
    Combine frontmatter metadata with CI results into one registry record.
    """
    meta = parse_frontmatter(example_path / "README.md")
    health, warning = compute_health(results)

    # Build the compatibility map — only record versions that were actually tested.
    compat = {}
    for version in ("stable", "main", "rc"):
        r = results.get(version)
        if r is None or r.get("skipped"):
            compat[version] = "untested"
        else:
            compat[version] = "pass" if r.get("passed") else "fail"

    return {
        "id": example_id,
        "name": meta.get("title", example_id),
        "meta": {
            "status": meta.get("status", "incubator"),
            "complexity": meta.get("complexity", "beginner"),
        },
        "ci": {
            "health": health,
            "warning": warning,
            "last_run": date.today().isoformat(),
        },
        "compatibility": compat,
    }


# ---------------------------------------------------------------------------
# Change detection helper
# ---------------------------------------------------------------------------


def meaningful_change(old: dict, new: dict) -> bool:
    """
    Return True if anything other than the last_run date is different.
    We skip last_run in the comparison so a pure date bump does not trigger
    a write — the file is only updated when the actual health or metadata changed.
    """

    def strip_date(record: dict) -> dict:
        stripped = {k: v for k, v in record.items() if k != "ci"}
        ci_no_date = {k: v for k, v in record.get("ci", {}).items() if k != "last_run"}
        stripped["ci"] = ci_no_date
        return stripped

    return strip_date(old) != strip_date(new)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update per-example registry files from run results."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing result JSON files from run_example.py",
    )
    parser.add_argument(
        "--registry-dir",
        default="registry",
        help="Output directory for per-example registry JSON files",
    )
    parser.add_argument(
        "--examples-dir",
        default="examples",
        help="Root directory that contains example subdirectories",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    registry_dir = Path(args.registry_dir)
    examples_dir = Path(args.examples_dir)

    registry_dir.mkdir(parents=True, exist_ok=True)

    all_results = load_results(results_dir)

    # Walk every example directory, not just ones that have results.
    # Examples with no results end up as "untested".
    for example_path in sorted(examples_dir.iterdir()):
        if not example_path.is_dir():
            continue

        example_id = example_path.name
        results = all_results.get(example_id, {})
        new_record = build_record(example_id, example_path, results)
        registry_file = registry_dir / f"{example_id}.json"

        if registry_file.exists():
            try:
                old_record = json.loads(registry_file.read_text(encoding="utf-8"))
                if not meaningful_change(old_record, new_record):
                    print(f"  unchanged  {example_id}")
                    continue
            except (json.JSONDecodeError, KeyError, TypeError):
                # Unreadable or malformed file — overwrite it.
                pass

        registry_file.write_text(json.dumps(new_record, indent=2), encoding="utf-8")
        print(f"  updated    {example_id}")


if __name__ == "__main__":
    main()
