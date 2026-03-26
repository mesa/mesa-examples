#!/usr/bin/env python3
# Finds all Mesa example directories by scanning for marker files.

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
    """Return sorted list of example directory paths relative to root."""
    examples = set()
    root_path = Path(root)

    for marker in MARKER_FILES:
        for p in root_path.rglob(marker):
            parent = p.parent
            # collapse A/A patterns (e.g. el_farol/el_farol -> el_farol)
            if parent.name == parent.parent.name:
                parent = parent.parent
            # skip infra and hidden dirs
            if any(part in SKIP_DIRS or part.startswith(".") for part in parent.parts):
                continue
            examples.add(str(parent.relative_to(root_path)))

    # deduplicate: keep only outermost paths
    result = sorted(examples)
    filtered = []
    for ex in result:
        if not any(ex.startswith(prev + "/") for prev in filtered):
            filtered.append(ex)
    return filtered


def find_example_root(filepath, repo_root="."):
    """Walk up from filepath to find the nearest example directory, or None."""
    path = Path(filepath)
    repo = Path(repo_root)

    for parent in path.parents:
        if parent == repo or parent == Path("."):
            break
        if any(part in SKIP_DIRS or part.startswith(".") for part in parent.parts):
            break
        if any((parent / m).exists() for m in MARKER_FILES):
            return str(parent)
    return None
