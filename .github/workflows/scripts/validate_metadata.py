"""Validate metadata.toml files in all examples."""

import sys
from pathlib import Path

import tomllib

REQUIRED_FIELDS = [
    "title",
    "abstract",
    "authors",
    "domain",
    "space",
    "time",
    "complexity",
    "keywords",
    "mesa",
]

ALLOWED_SPACE = {"Grid", "Network", "Continuous", "None"}
ALLOWED_TIME = {"Discrete", "Continuous"}
ALLOWED_COMPLEXITY = {"Basic", "Advanced"}

errors = []
examples_dir = Path("examples")

metadata_files = list(examples_dir.glob("*/metadata.toml"))

if not metadata_files:
    print("No metadata.toml files found.")
    sys.exit(0)

for path in metadata_files:
    example = path.parent.name
    with open(path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            errors.append(f"{example}: Invalid TOML - {e}")
            continue

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"{example}: Missing required field '{field}'")

    if "space" in data and data["space"] not in ALLOWED_SPACE:
        errors.append(
            f"{example}: 'space' must be one of {ALLOWED_SPACE}, got '{data['space']}'"
        )

    if "time" in data and data["time"] not in ALLOWED_TIME:
        errors.append(
            f"{example}: 'time' must be one of {ALLOWED_TIME}, got '{data['time']}'"
        )

    if "complexity" in data and data["complexity"] not in ALLOWED_COMPLEXITY:
        errors.append(
            f"{example}: 'complexity' must be one of {ALLOWED_COMPLEXITY}, "
            f"got '{data['complexity']}'"
        )

if errors:
    print("Metadata validation FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"All {len(metadata_files)} metadata.toml files are valid.")
