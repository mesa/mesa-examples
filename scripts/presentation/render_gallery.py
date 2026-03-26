#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


# Convert internal health value → readable label for the table
def health_label(h):
    return {
        "passing": "✅ Passing",
        "warning": "⚠️ Warning",
        "broken": "🚨 Broken",
        "untested": "⬜ Untested",
    }.get(h, h)


# Build "Works On" column by including only versions where example passes
def works_on(compat):
    works = []
    if compat.get("stable") == "pass":
        works.append("stable")
    if compat.get("main") == "pass":
        works.append("main")
    if compat.get("rc") == "pass":
        works.append("rc")
    return ", ".join(works) if works else "—"


# Load all per-example registry JSON files into memory
def load_registry(registry_dir):
    records = []
    for f in sorted(Path(registry_dir).glob("*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"Skipping malformed registry file {f}: {e}")
            continue
    return records


# Group examples by status so we can render sections (showcase → standard → incubator)
def group_by_status(records):
    groups = {"showcase": [], "standard": [], "incubator": []}
    for r in records:
        status = r.get("meta", {}).get("status", "incubator")
        groups.setdefault(status, []).append(r)
    return groups


# Count health states for summary line at the top
def counts(records):
    c = {"passing": 0, "warning": 0, "broken": 0}
    for r in records:
        h = r.get("ci", {}).get("health")
        if h in c:
            c[h] += 1
    return c


# Render one table (used for each section)
def render_table(rows):
    if not rows:
        return "_No examples_\n"

    out = []
    out.append("| Example | Health | Complexity | Works On |")
    out.append("|--------|--------|-----------|----------|")

    for r in rows:
        name = r.get("name", r.get("location", r.get("id", "Unknown")))
        health = health_label(r.get("ci", {}).get("health"))
        complexity = r.get("meta", {}).get("complexity", "-")
        compat = works_on(r.get("compatibility", {}))

        out.append(f"| {name} | {health} | {complexity} | {compat} |")

    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # Read all example states from registry
    records = load_registry(args.registry_dir)

    # Sort for stable output (avoids noisy diffs in CI)
    records.sort(
        key=lambda r: r.get("name", r.get("location", r.get("id", ""))).lower()
    )

    stats = counts(records)
    groups = group_by_status(records)

    today = datetime.now(timezone.utc).date().isoformat()

    content = []

    # Header section (context + summary)
    content.append("# Mesa Examples\n")
    content.append(
        "_A curated collection of Mesa examples, automatically validated by CI._\n"
    )
    content.append(f"_Last updated: {today}_\n")
    content.append(
        f"**{len(records)} examples** · "
        f"✅ {stats['passing']} Passing · "
        f"⚠️ {stats['warning']} Warning · "
        f"🚨 {stats['broken']} Broken\n"
    )

    # Render each section in priority order
    content.append("\n---\n")
    content.append("## 🌟 Showcase\n")
    content.append(render_table(groups.get("showcase", [])))

    content.append("\n## 📦 Standard\n")
    content.append(render_table(groups.get("standard", [])))

    content.append("\n## 🧪 Incubator\n")
    content.append(render_table(groups.get("incubator", [])))

    # Overwrite the gallery file completely each run
    Path(args.output).write_text("\n".join(content), encoding="utf-8")


if __name__ == "__main__":
    main()
