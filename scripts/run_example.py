#!/usr/bin/env python3
# Runs a single Mesa example and writes a JSON result file.
# Used by both PR and scheduled CI workflows.

import argparse
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import yaml


def _find_readme(example_path: Path) -> Path | None:
    """Find README regardless of casing (README.md, Readme.md, etc)."""
    for f in example_path.iterdir():
        if f.is_file() and f.name.lower() == "readme.md":
            return f
    return None


def parse_frontmatter(example_path: Path) -> dict:
    """Read YAML frontmatter from the example's README."""
    readme = _find_readme(example_path)
    if readme is None:
        return {}
    text = readme.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    close = text.find("\n---", 3)
    if close == -1:
        return {}
    try:
        return yaml.safe_load(text[3:close]) or {}
    except yaml.YAMLError:
        return {}


def first_warning(stderr_text: str) -> "str | None":
    """Return the first warning line from stderr, trimmed to 100 chars."""
    for line in stderr_text.splitlines():
        stripped = line.strip()
        if "warning" in stripped.lower():
            return stripped[:100]
    return None


def _make_env(example_path: Path) -> dict:
    """Build env dict with PYTHONPATH covering example root and its parent."""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(example_path.resolve()),
            str(example_path.resolve().parent),
        ]
    )
    return env


def run_script(script_path: Path, example_path: Path, timeout: int = 30) -> dict:
    """Run a .py file directly as a script from the example root."""
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path.resolve())],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(example_path.resolve()),
            env=_make_env(example_path),
            check=False,
        )
        passed = proc.returncode == 0
        error = proc.stderr.strip()[-1000:] if not passed else None
        return {"passed": passed, "warning": first_warning(proc.stderr), "error": error}
    except subprocess.TimeoutExpired:
        # timeout on an app = it stayed alive = pass
        return {"passed": True, "warning": None, "error": None}
    except Exception as exc:
        return {"passed": False, "warning": None, "error": str(exc)[-1000:]}


def run_module(module_name: str, example_path: Path, timeout: int = 30) -> dict:
    """Run a module with -m from the parent directory."""
    parent = example_path.resolve().parent
    env = _make_env(example_path)
    # also add the parent to PYTHONPATH for nested package resolution
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(example_path.resolve()),
            str(parent),
        ]
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-m", module_name],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(parent),
            env=env,
            check=False,
        )
        passed = proc.returncode == 0
        error = proc.stderr.strip()[-1000:] if not passed else None
        return {"passed": passed, "warning": first_warning(proc.stderr), "error": error}
    except subprocess.TimeoutExpired:
        return {"passed": True, "warning": None, "error": None}
    except Exception as exc:
        return {"passed": False, "warning": None, "error": str(exc)[-1000:]}


def run_fallback(example_path: Path) -> dict:
    """Import model.py in a subprocess, find a Model subclass, run 5 steps."""
    # find model.py in root or nested subfolder
    model_py = example_path / "model.py"
    subfolder = example_path / example_path.name
    if not model_py.exists() and (subfolder / "model.py").exists():
        model_py = subfolder / "model.py"

    if not model_py.exists():
        return {
            "passed": False,
            "warning": None,
            "error": "No run.py, app.py, or model.py found.",
        }

    # use importlib.import_module so relative imports work inside packages
    root_str = str(example_path.resolve())
    parent_str = str(example_path.resolve().parent)

    runner = textwrap.dedent(f"""\
import json, sys, warnings as _w, traceback

sys.path.insert(0, {root_str!r})
sys.path.insert(1, {parent_str!r})

_warn = None
_orig = _w.showwarning
def _cap(msg, cat, fn, ln, file=None, line=None):
    global _warn
    if _warn is None: _warn = str(msg)[:100]
_w.showwarning = _cap

try:
    import importlib.util, importlib
    spec = importlib.util.spec_from_file_location("_model", {str(model_py.resolve())!r},
        submodule_search_locations=[{str(model_py.parent.resolve())!r}])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_model"] = mod
    # register the parent package so relative imports work
    parent_pkg = {str(model_py.parent.name)!r}
    if parent_pkg not in sys.modules:
        import types
        pkg = types.ModuleType(parent_pkg)
        pkg.__path__ = [{str(model_py.parent.resolve())!r}]
        pkg.__package__ = parent_pkg
        sys.modules[parent_pkg] = pkg
    mod.__package__ = parent_pkg
    spec.loader.exec_module(mod)

    import mesa
    cls = None
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and issubclass(obj, mesa.Model) and obj is not mesa.Model:
            cls = obj
            break

    if cls is None or not callable(getattr(cls, "step", None)):
        print(json.dumps({{"passed": False, "warning": None,
              "error": "No mesa.Model subclass found."}}))
        sys.exit(0)

    try:
        m = cls()
    except TypeError:
        print(json.dumps({{"passed": False, "warning": _warn,
              "error": "Model needs constructor args. Add run.py."}}))
        sys.exit(0)

    for _ in range(5): m.step()
    print(json.dumps({{"passed": True, "warning": _warn, "error": None}}))
except Exception:
    print(json.dumps({{"passed": False, "warning": _warn,
          "error": traceback.format_exc()[-1000:]}}))
""")

    try:
        proc = subprocess.run(
            [sys.executable, "-c", runner],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if lines:
            result = json.loads(lines[-1])
            if result["warning"] is None:
                result["warning"] = first_warning(proc.stderr)
            return result
        return {
            "passed": False,
            "warning": None,
            "error": proc.stderr.strip()[-1000:] or "No output from fallback",
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "warning": None, "error": "Timeout after 30s"}
    except Exception as exc:
        return {"passed": False, "warning": None, "error": str(exc)[-1000:]}


def _has_relative_imports(filepath: Path) -> bool:
    """Quick check if a .py file uses relative imports (from .xxx)."""
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("from ."):
                return True
    except Exception:
        return False
    return False


def _imports_own_package(filepath: Path, pkg_name: str) -> bool:
    """Check if a .py file imports its own package name (e.g. 'from hotelling_law.agents')."""
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith((f"from {pkg_name}.", f"import {pkg_name}.")):
                return True
    except Exception:
        return False
    return False


def find_and_run(example_path: Path) -> dict:
    """Find the best entry point and run it with the right strategy."""
    subfolder = example_path / example_path.name

    # collect entry points: (path, is_app)
    candidates = []
    for name, is_app in [("run.py", False), ("app.py", True)]:
        if (example_path / name).exists():
            candidates.append((example_path / name, is_app))
        if (subfolder / name).exists():
            candidates.append((subfolder / name, is_app))

    if not candidates:
        return run_fallback(example_path)

    script_path, is_app = candidates[0]
    timeout = 45 if is_app else 30

    # Always prefer script execution first (more reliable)
    result = run_script(script_path, example_path, timeout)

    # If it fails and looks like import issue → fallback to module
    if not result["passed"] and (
        "ImportError" in (result.get("error") or "")
        or "ModuleNotFoundError" in (result.get("error") or "")
    ):
        return run_module(
            str(script_path.relative_to(example_path.parent).with_suffix("")).replace(
                os.sep, "."
            ),
            example_path,
            timeout,
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Mesa example.")
    parser.add_argument("example_dir", help="Path to the example directory")
    parser.add_argument("--version", required=True, help="stable | main | rc")
    parser.add_argument("--output", required=True, help="JSON result path")
    args = parser.parse_args()

    example_path = Path(args.example_dir)
    if not example_path.is_dir():
        print(f"Error: {example_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    example_id = str(example_path).replace(os.sep, "/").strip("/")

    # check for ci.skip in README frontmatter
    meta = parse_frontmatter(example_path)
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
        run_result = find_and_run(example_path)
        result = {
            "example_id": example_id,
            "version": args.version,
            "passed": run_result["passed"],
            "skipped": False,
            "warning": run_result.get("warning"),
            "error": run_result.get("error"),
        }

    # write result JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # print human-readable status for CI logs
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
