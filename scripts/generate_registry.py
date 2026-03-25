#!/usr/bin/env python3
import argparse
import glob
import json
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing stable/ and main/ JSON results",
    )
    parser.add_argument(
        "--registry-dir", required=True, help="Directory to output registry JSON files"
    )
    args = parser.parse_args()

    os.makedirs(args.registry_dir, exist_ok=True)

    stable_results = {}
    for f in glob.glob(os.path.join(args.results_dir, "stable", "*.json")):
        with open(f) as fp:
            data = json.load(fp)
            if "id" in data:
                stable_results[data["id"]] = data

    main_results = {}
    for f in glob.glob(os.path.join(args.results_dir, "main", "*.json")):
        with open(f) as fp:
            data = json.load(fp)
            if "id" in data:
                main_results[data["id"]] = data

    all_ids = set(stable_results.keys()).union(main_results.keys())
    today = datetime.now().strftime("%Y-%m-%d")

    for ex_id in all_ids:
        stable = stable_results.get(ex_id, {})
        main_res = main_results.get(ex_id, {})

        base = stable if stable else main_res

        stable_status = stable.get("status", "untested")
        main_status = main_res.get("status", "untested")

        warning = stable.get("warning") or main_res.get("warning")

        if stable_status == "broken":
            health = "broken"
        elif (stable_status == "passing" and main_status == "broken") or warning:
            health = "warning"
        elif stable_status == "passing" and main_status == "passing":
            health = "passing"
        else:
            if stable_status == "untested" and main_status == "untested":
                health = "untested"
            elif stable_status == "warning" or main_status == "warning":
                health = "warning"
            else:
                health = "passing" if stable_status == "passing" else "broken"

        new_data = {
            "id": ex_id,
            "name": base.get("meta", {}).get("title", ex_id),
            "meta": {
                "status": base.get("meta", {}).get("status", "incubator").lower(),
                "complexity": base.get("meta", {})
                .get("complexity", "intermediate")
                .lower(),
            },
            "ci": {"health": health, "warning": warning, "last_run": today},
            "compatibility": {
                "stable": "fail"
                if stable_status == "broken"
                else "pass"
                if stable_status in ["passing", "warning"]
                else "untested",
                "main": "fail"
                if main_status == "broken"
                else "pass"
                if main_status in ["passing", "warning"]
                else "untested",
                "rc": "untested",
            },
        }

        registry_file = os.path.join(args.registry_dir, f"{ex_id}.json")
        write_it = True

        if os.path.exists(registry_file):
            with open(registry_file) as f:
                try:
                    old_data = json.load(f)
                    old_compare = dict(old_data)
                    new_compare = dict(new_data)
                    if "ci" in old_compare:
                        old_compare["ci"]["last_run"] = ""
                    new_compare["ci"]["last_run"] = ""
                    if old_compare == new_compare:
                        write_it = False
                except json.JSONDecodeError:
                    pass

        if write_it:
            with open(registry_file, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2)


if __name__ == "__main__":
    main()
