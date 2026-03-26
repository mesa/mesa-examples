#!/usr/bin/env python3
# Manages a single GitHub issue that tracks CI health failures.
#
# Rules (from spec):
#   - Open or update the issue when:
#       (status == showcase AND health in {warning, broken})
#       OR (status == standard AND health == broken)
#   - Keep it as a single grouped issue (never duplicate).
#   - Close it when all standard + showcase examples are passing.
#
# Usage:
#   python scripts/issue_manager.py \
#       --registry-dir registry/ \
#       --repo owner/repo-name
#
# Requires GITHUB_TOKEN env var (write:issues scope).

import argparse
import json
import os
import sys
from pathlib import Path

import requests  # pip install requests

ISSUE_TITLE = "CI Health: Example Failures Detected"
ISSUE_LABEL = "ci-health"
GH_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def load_registries(registry_dir: Path) -> list:
    records = []
    for f in sorted(registry_dir.glob("*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return records


def should_flag(r: dict) -> bool:
    """True if this example needs to appear in the failure issue."""
    status = r.get("meta", {}).get("status", "")
    health = r.get("ci", {}).get("health", "untested")
    if status == "showcase" and health in ("warning", "broken"):
        return True
    return bool(status == "standard" and health == "broken")


def all_clear(records: list) -> bool:
    """
    True when no standard or showcase example is in a failing/warning state.
    Untested (ci.skip) examples are treated as OK — they were explicitly excluded.
    """
    for r in records:
        status = r.get("meta", {}).get("status", "")
        if status in ("standard", "showcase"):
            health = r.get("ci", {}).get("health", "untested")
            if health in ("warning", "broken"):
                return False
    return True


# ---------------------------------------------------------------------------
# Issue body builder
# ---------------------------------------------------------------------------


def build_body(flagged: list) -> str:
    lines = [
        "The following examples need attention:\n",
        "| Example | Status | Health | Warning |",
        "| ------- | ------ | ------ | ------- |",
    ]
    for r in sorted(flagged, key=lambda x: x.get("location", x.get("id", ""))):
        ex_id = r.get("location", r.get("id", "Unknown"))
        status = r.get("meta", {}).get("status", "")
        health = r.get("ci", {}).get("health", "")
        warning = r.get("ci", {}).get("warning") or "—"
        lines.append(f"| `{ex_id}` | {status} | **{health}** | {warning} |")
    lines.append("")
    lines.append("_Last updated automatically by scheduled CI._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }


def ensure_label(repo: str, token: str) -> None:
    """Create the ci-health label if it does not exist on this repo."""
    url = f"{GH_API}/repos/{repo}/labels/{ISSUE_LABEL}"
    resp = requests.get(url, headers=_headers(token), timeout=15)
    if resp.status_code == 404:
        requests.post(
            f"{GH_API}/repos/{repo}/labels",
            headers=_headers(token),
            json={
                "name": ISSUE_LABEL,
                "color": "d93f0b",
                "description": "CI health tracking",
            },
            timeout=15,
        )


def find_existing_issue(repo: str, token: str) -> "dict | None":
    """Find the one open issue with our label and title, or return None."""
    url = f"{GH_API}/repos/{repo}/issues"
    params = {"state": "open", "labels": ISSUE_LABEL, "per_page": 25}
    resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
    resp.raise_for_status()
    for issue in resp.json():
        if issue.get("title") == ISSUE_TITLE:
            return issue
    return None


def create_issue(repo: str, token: str, body: str) -> None:
    url = f"{GH_API}/repos/{repo}/issues"
    payload = {"title": ISSUE_TITLE, "body": body, "labels": [ISSUE_LABEL]}
    resp = requests.post(url, headers=_headers(token), json=payload, timeout=15)
    resp.raise_for_status()
    print(f"  created issue #{resp.json()['number']}")


def update_issue(repo: str, token: str, issue_number: int, body: str) -> None:
    url = f"{GH_API}/repos/{repo}/issues/{issue_number}"
    resp = requests.patch(url, headers=_headers(token), json={"body": body}, timeout=15)
    resp.raise_for_status()
    print(f"  updated issue #{issue_number}")


def close_issue(repo: str, token: str, issue_number: int) -> None:
    url = f"{GH_API}/repos/{repo}/issues/{issue_number}"
    resp = requests.patch(
        url,
        headers=_headers(token),
        json={"state": "closed"},
        timeout=15,
    )
    resp.raise_for_status()
    print(f"  closed issue #{issue_number} (all clear)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create, update, or close the CI health issue on GitHub."
    )
    parser.add_argument("--registry-dir", default="registry")
    parser.add_argument("--repo", required=True, help="owner/repo-name")
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token (defaults to $GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    if not args.token:
        print(
            "Error: no GitHub token. Set GITHUB_TOKEN or pass --token.", file=sys.stderr
        )
        sys.exit(1)

    registry_dir = Path(args.registry_dir)
    records = load_registries(registry_dir)

    if not records:
        print("No registry files found — nothing to check.")
        return

    flagged = [r for r in records if should_flag(r)]

    # Make sure the label exists before we try to attach it to an issue.
    try:
        ensure_label(args.repo, args.token)
    except requests.RequestException as exc:
        print(f"Warning: could not ensure label exists: {exc}", file=sys.stderr)

    existing = find_existing_issue(args.repo, args.token)

    if all_clear(records):
        if existing:
            close_issue(args.repo, args.token, existing["number"])
        else:
            print("  all clear — no open issue to close")
        return

    # There are failures that need attention.
    body = build_body(flagged)

    if existing:
        update_issue(args.repo, args.token, existing["number"], body)
    else:
        create_issue(args.repo, args.token, body)


if __name__ == "__main__":
    main()
