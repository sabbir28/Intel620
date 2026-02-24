#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
CHANGELOG = ROOT / "CHANGELOG.md"
README_TEMPLATE = ROOT / "docs" / "README.template.md"
README = ROOT / "README.md"


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    body: str


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def get_last_tag() -> str | None:
    try:
        return run("git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*.[0-9]*.[0-9]*")
    except subprocess.CalledProcessError:
        return None


def get_commits(since_tag: str | None) -> list[Commit]:
    range_expr = f"{since_tag}..HEAD" if since_tag else "HEAD"
    raw = run("git", "log", range_expr, "--pretty=format:%H%x1f%s%x1f%b%x1e")
    commits: list[Commit] = []
    for block in raw.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        parts = [part.strip() for part in block.split("\x1f", 2)]
        if len(parts) == 2:
            parts.append("")
        if len(parts) != 3:
            continue
        sha, subject, body = parts
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def bump_kind(commits: list[Commit]) -> str | None:
    bump = None
    for commit in commits:
        if "BREAKING CHANGE" in commit.body or re.search(r"!:", commit.subject):
            return "major"
        if commit.subject.startswith("feat"):
            bump = "minor"
        elif commit.subject.startswith("fix") and bump != "minor":
            bump = "patch"
    return bump


def parse_version(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def next_version(current: str, bump: str) -> str:
    major, minor, patch = parse_version(current)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return current


def update_pyproject(version: str) -> None:
    content = PYPROJECT.read_text(encoding="utf-8")
    updated = re.sub(r'(?m)^version = "[0-9]+\.[0-9]+\.[0-9]+"$', f'version = "{version}"', content)
    PYPROJECT.write_text(updated, encoding="utf-8")


def render_changelog(version: str, commits: list[Commit]) -> str:
    date = dt.date.today().isoformat()
    feat = [c for c in commits if c.subject.startswith("feat")]
    fix = [c for c in commits if c.subject.startswith("fix")]
    other = [c for c in commits if c not in feat and c not in fix]

    lines = [f"## v{version} - {date}", ""]
    if feat:
        lines.extend(["### Features", ""])
        lines.extend([f"- {c.subject} ({c.sha[:7]})" for c in feat])
        lines.append("")
    if fix:
        lines.extend(["### Fixes", ""])
        lines.extend([f"- {c.subject} ({c.sha[:7]})" for c in fix])
        lines.append("")
    if other:
        lines.extend(["### Maintenance", ""])
        lines.extend([f"- {c.subject} ({c.sha[:7]})" for c in other])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepend_changelog(section: str) -> None:
    if CHANGELOG.exists():
        existing = CHANGELOG.read_text(encoding="utf-8")
    else:
        existing = "# Changelog\n\n"
    if not existing.startswith("# Changelog"):
        existing = "# Changelog\n\n" + existing
    updated = existing.rstrip() + "\n"
    marker = "# Changelog\n\n"
    body = updated[len(marker) :]
    CHANGELOG.write_text(marker + section + "\n" + body.lstrip(), encoding="utf-8")


def update_readme(version: str) -> None:
    template = README_TEMPLATE.read_text(encoding="utf-8")
    rendered = template.format(version=version, date=dt.date.today().isoformat())
    README.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()

    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    current = project["project"]["version"]
    last_tag = get_last_tag()
    commits = get_commits(last_tag)
    bump = bump_kind(commits)

    if not bump:
        args.github_output.write_text("release_created=false\n", encoding="utf-8")
        print("No releasable commits found.")
        return 0

    version = next_version(current, bump)
    tag = f"v{version}"

    try:
        run("git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}")
        raise RuntimeError(f"Tag {tag} already exists; tags are immutable.")
    except subprocess.CalledProcessError:
        pass

    update_pyproject(version)
    section = render_changelog(version, commits)
    prepend_changelog(section)
    update_readme(version)

    args.github_output.write_text(
        f"release_created=true\nversion={version}\ntag={tag}\nbump={bump}\n",
        encoding="utf-8",
    )
    print(f"Prepared release {tag} ({bump}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
