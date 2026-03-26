#!/usr/bin/env python3
# Render GALLERY.md from registry results.

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def health_label(h):
    """Convert health status to a readable label with emoji."""
    return {
        "passing": "✅ Passing",
        "warning": "⚠️ Warning",
        "broken": "🚨 Broken",
        "untested": "⬜ Untested",
    }.get(h, h)


def works_on(compat):
    """List versions where the example passes."""
    works = [v for v in ("stable", "main", "rc") if compat.get(v) == "pass"]
    return ", ".join(works) if works else "—"


def load_registry(registry_dir):
    """Load all JSON records from the registry directory."""
    records = []
    for f in sorted(Path(registry_dir).glob("*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"Skipping malformed registry file {f}: {e}")
    return records


def group_by_status(records):
    """Group examples by their status (showcase, standard, incubator)."""
    groups = {"showcase": [], "standard": [], "incubator": []}
    for r in records:
        status = r.get("meta", {}).get("status", "incubator")
        groups.setdefault(status, []).append(r)
    return groups


def counts(records):
    """Count occurrences of each health state."""
    c = {"passing": 0, "warning": 0, "broken": 0}
    for r in records:
        h = r.get("ci", {}).get("health")
        if h in c:
            c[h] += 1
    return c


def render_table(rows):
    """Generate a markdown table for a list of example records."""
    if not rows:
        return "_No examples_\n"
    out = [
        "| Example | Health | Complexity | Works On |",
        "|--------|--------|-----------|----------|",
    ]
    for r in rows:
        name = r.get("name", r.get("location", "Unknown"))
        location = r.get("location", "")
        # Link the name to its directory if we have a location
        md_name = f"[{name}]({location})" if location else name

        health = health_label(r.get("ci", {}).get("health"))
        complexity = r.get("meta", {}).get("complexity", "-")
        compat = works_on(r.get("compatibility", {}))
        out.append(f"| {md_name} | {health} | {complexity} | {compat} |")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = load_registry(args.registry_dir)
    records.sort(key=lambda r: r.get("name", r.get("location", "")).lower())

    stats = counts(records)
    groups = group_by_status(records)
    today = datetime.now(timezone.utc).date().isoformat()

    content = [
        "# Mesa Examples\n",
        "_A curated collection of Mesa examples, automatically validated by CI._\n",
        f"_Last updated: {today}_\n",
        f"**{len(records)} examples** · ✅ {stats['passing']} Passing · ⚠️ {stats['warning']} Warning · 🚨 {stats['broken']} Broken\n",
        "\n---\n",
        "## 🌟 Showcase\n",
        render_table(groups.get("showcase", [])),
        "\n## 📦 Standard\n",
        render_table(groups.get("standard", [])),
        "\n## 🧪 Incubator\n",
        render_table(groups.get("incubator", [])),
    ]

    Path(args.output).write_text("\n".join(content), encoding="utf-8")


if __name__ == "__main__":
    main()
