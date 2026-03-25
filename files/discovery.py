#!/usr/bin/env python3
"""Shared example discovery logic for CI scripts.

An example is any directory containing at least one marker file:
model.py, run.py, or app.py.

This module is imported by detect_changes.py, and can be invoked
inline from CI workflow YAML via:
    python -c 'from files.discovery import discover_all_examples; ...'
"""

from pathlib import Path

MARKER_FILES = ("model.py", "run.py", "app.py")
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".github",
    "scripts",
    "files",
    "pulls",
    "node_modules",
}


def discover_all_examples(root="."):
    """Find all example directories under *root*.

    Returns a sorted list of relative paths (e.g. ``["examples/forest_fire",
    "gis/geo_schelling"]``).  Nested duplicates are removed — if both
    ``examples/foo`` and ``examples/foo/foo`` contain a marker, only the
    shorter (outermost) path is kept.
    """
    examples = set()
    root_path = Path(root)

    for marker in MARKER_FILES:
        for p in root_path.rglob(marker):
            parent = p.parent
            # Mesa Pattern: Many examples put their code in a subfolder with the
            # same name (e.g. examples/el_farol/el_farol/model.py).
            # We want the example root to be the top-level folder (A/A -> A).
            if parent.name == parent.parent.name:
                parent = parent.parent

            # Skip directories that live inside infrastructure folders or
            # hidden directories (e.g. .git, .github).
            if any(part in SKIP_DIRS or part.startswith(".") for part in parent.parts):
                continue
            examples.add(str(parent.relative_to(root_path)))

    # Deduplicate nested paths: keep only the outermost example root.
    result = sorted(examples)
    filtered = []
    for ex in result:
        if not any(ex.startswith(prev + "/") for prev in filtered):
            filtered.append(ex)
    return filtered


def find_example_root(filepath, repo_root="."):
    """Walk up from *filepath* to find the nearest example directory.

    Returns the relative path string of the example root, or ``None``
    if the file does not belong to any example.
    """
    path = Path(filepath)
    repo = Path(repo_root)

    for parent in path.parents:
        if parent == repo or parent == Path("."):
            break
        if any(part in SKIP_DIRS or part.startswith(".") for part in parent.parts):
            break
        if any((repo / parent / m).exists() for m in MARKER_FILES):
            return str(parent)
    return None
