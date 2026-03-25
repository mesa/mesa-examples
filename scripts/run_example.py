#!/usr/bin/env python3
# Runs a single Mesa example and writes the result to a JSON file.
# Called by both PR and scheduled CI workflows.
#
# Usage:
#   python scripts/run_example.py examples/wolf_sheep \
#       --version stable \
#       --output results/wolf_sheep_stable.json

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml  # pip install pyyaml

# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------


def parse_frontmatter(readme_path: Path) -> dict:
    """
    Pull YAML frontmatter out of a README.md.
    Returns an empty dict if there is no frontmatter block or the file is missing.
    """
    if not readme_path.exists():
        return {}
    text = readme_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    # Find the closing --- on its own line (skip the opening one at index 0)
    close = text.find("\n---", 3)
    if close == -1:
        return {}
    try:
        return yaml.safe_load(text[3:close]) or {}
    except yaml.YAMLError:
        return {}


# ---------------------------------------------------------------------------
# Warning capture helper
# ---------------------------------------------------------------------------


def first_warning(stderr_text: str) -> "str | None":
    """
    Scan Python stderr output for the first line that mentions a Warning.
    Returns that line trimmed to 100 characters, or None if nothing found.
    """
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if "warning" in stripped.lower():
            return stripped[:100]
    return None


# ---------------------------------------------------------------------------
# Execution path 1: run.py exists
# ---------------------------------------------------------------------------


def run_via_run_py(run_py: Path, cwd: Path) -> dict:
    """
    Execute the example's run.py in a subprocess with a 30-second timeout.
    Captures returncode and any warning text from stderr.
    """
    try:
        proc = subprocess.run(
            [sys.executable, str(run_py.resolve())],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cwd.resolve()),
            check=False,
        )
        passed = proc.returncode == 0
        warning = first_warning(proc.stderr)
        # Only store the error text if the run actually failed
        error = proc.stderr.strip()[:200] if not passed else None
        return {"passed": passed, "warning": warning, "error": error}
    except subprocess.TimeoutExpired:
        return {"passed": False, "warning": None, "error": "Timeout after 30 seconds"}
    except Exception as exc:
        return {"passed": False, "warning": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Execution path 2: app.py exists (visualization startup check)
# ---------------------------------------------------------------------------


def run_via_app_py(app_py: Path, cwd: Path) -> dict:
    """Start app.py and verify it doesn't crash immediately.

    Timeout = PASS (app is running and serving).
    Crash   = FAIL.
    """
    try:
        proc = subprocess.run(
            [sys.executable, str(app_py.resolve())],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(cwd.resolve()),
            check=False,
        )
        # If we reach here, the process exited before timeout.
        # Non-zero is definitely a crash.
        if proc.returncode != 0:
            return {
                "passed": False,
                "warning": first_warning(proc.stderr),
                "error": proc.stderr.strip()[:200] or "app.py exited with error",
            }
        # Exited cleanly before timeout — treat as pass
        return {
            "passed": True,
            "warning": first_warning(proc.stderr),
            "error": None,
        }
    except subprocess.TimeoutExpired:
        # Timeout means the app started and stayed running → PASS
        return {"passed": True, "warning": None, "error": None}
    except Exception as exc:
        return {"passed": False, "warning": None, "error": str(exc)[:200]}


# ---------------------------------------------------------------------------
# Execution path 3: fallback (no run.py or app.py)
# ---------------------------------------------------------------------------


def run_via_fallback(example_path: Path) -> dict:
    """
    No run.py found. Import model.py in a child process, instantiate the
    Model class, call step() five times, and report the outcome.

    Running in a child process keeps imports isolated and lets us capture
    warnings without polluting this process's warning filters.

    If the model requires constructor arguments or there is no Model class,
    we return an error that tells the author to add a run.py.
    """
    model_py = example_path / "model.py"
    if not model_py.exists():
        return {
            "passed": False,
            "warning": None,
            "error": "No run.py, app.py, or model.py found. Add run.py for reliable execution.",
        }

    # Build a self-contained runner that prints a single JSON line to stdout.
    # We use repr() for the paths so any OS-specific characters are safely escaped.
    runner_script = textwrap.dedent(f"""\
import json
import sys
import warnings as _w

sys.path.insert(0, {str(example_path.resolve())!r})

_first_warning = None

_original = _w.showwarning
def _capture(msg, category, filename, lineno, file=None, line=None):
    global _first_warning
    if _first_warning is None:
        _first_warning = str(msg)[:100]
_w.showwarning = _capture

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("model", {str(model_py.resolve())!r})
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    model_cls = getattr(mod, "Model", None)
    if not (isinstance(model_cls, type) and callable(getattr(model_cls, "step", None))):
        print(json.dumps({{
            "passed": False, "warning": None,
            "error": "No Model class found. Add run.py for reliable execution."
        }}))
        sys.exit(0)

    try:
        instance = model_cls()
    except TypeError:
        print(json.dumps({{
            "passed": False,
            "warning": _first_warning,
            "error": "Model requires constructor arguments. Add run.py for reliable CI execution."
        }}))
        sys.exit(0)

    for _ in range(5):
        instance.step()

    print(json.dumps({{"passed": True, "warning": _first_warning, "error": None}}))

except Exception as exc:
    print(json.dumps({{
        "passed": False,
        "warning": _first_warning,
        "error": str(exc)[:200] + "\\nAdd run.py for reliable execution."
    }}))
""")

    try:
        proc = subprocess.run(
            [sys.executable, "-c", runner_script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # The last non-empty stdout line should be our JSON result.
        output_lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if output_lines:
            result = json.loads(output_lines[-1])
            # If the in-process capture missed something, check stderr too.
            if result["warning"] is None:
                result["warning"] = first_warning(proc.stderr)
            return result
        # Script crashed before printing anything.
        return {
            "passed": False,
            "warning": None,
            "error": proc.stderr.strip() or "Fallback runner produced no output",
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "warning": None, "error": "Timeout after 30 seconds"}
    except (json.JSONDecodeError, Exception) as exc:
        return {"passed": False, "warning": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one Mesa example and write a JSON result file."
    )
    parser.add_argument("example_dir", help="Path to the example directory")
    parser.add_argument(
        "--version",
        required=True,
        help="Mesa version label being tested: stable | main | rc",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Where to write the JSON result (e.g. results/wolf_sheep_stable.json)",
    )
    args = parser.parse_args()

    example_path = Path(args.example_dir)
    if not example_path.is_dir():
        print(f"Error: {example_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    example_id = str(example_path).replace(os.sep, "/").strip("/")

    # Check for ci.skip in the README frontmatter before doing anything else.
    meta = parse_frontmatter(example_path / "README.md")
    ci_config = meta.get("ci") or {}

    if ci_config.get("skip", False):
        result = {
            "example_id": example_id,
            "version": args.version,
            "passed": None,
            "skipped": True,
            "warning": None,
            "error": None,
        }
    else:
        run_py = example_path / "run.py"
        app_py = example_path / "app.py"
        if run_py.exists():
            run_result = run_via_run_py(run_py, example_path)
        elif app_py.exists():
            run_result = run_via_app_py(app_py, example_path)
        else:
            run_result = run_via_fallback(example_path)

        result = {
            "example_id": example_id,
            "version": args.version,
            "passed": run_result["passed"],
            "skipped": False,
            "warning": run_result.get("warning"),
            "error": run_result.get("error"),
        }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Human-readable status line for CI logs
    if result.get("skipped"):
        tag = "SKIP"
    elif result["passed"]:
        tag = "PASS"
    else:
        tag = "FAIL"
    print(f"{tag}  {example_id}  ({args.version})")
    if result.get("error"):
        print(f"     {result['error'][:120]}")

    if not result.get("passed") and not result.get("skipped"):
        sys.exit(1)


if __name__ == "__main__":
    main()
