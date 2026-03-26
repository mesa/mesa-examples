#!/usr/bin/env python3
"""Detect which examples a PR touches via git diff.

Outputs a JSON array of example directory paths to stdout.
If a shared file changed (outside any example), outputs '["ALL"]'
so the caller can expand it into every known example.

Usage (from repo root):
    python scripts/detect_changes.py origin/main HEAD
"""

import json
import subprocess
import sys

from discovery import find_example_root


def main():
    if len(sys.argv) < 3:
        print("Usage: detect_changes.py <base_ref> <head_ref>")
        sys.exit(1)

    base_ref = sys.argv[1]
    head_ref = sys.argv[2]

    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        # Cannot determine diff → safest to test everything.
        print(json.dumps(["ALL"]))
        sys.exit(0)

    changed_files = proc.stdout.splitlines()

    affected_examples = set()
    shared_changed = False

    for f in changed_files:
        # Pure documentation changes never trigger tests.
        # Only skip root-level docs
        if f.endswith(".md") and "/" not in f:
            continue
        root = find_example_root(f)
        if root:
            affected_examples.add(root)
        else:
            shared_changed = True

    if shared_changed:
        print(json.dumps(["ALL"]))
    else:
        print(json.dumps(sorted(affected_examples)))


if __name__ == "__main__":
    main()
