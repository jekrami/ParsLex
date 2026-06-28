#!/usr/bin/env python3
"""Bump ParsLex semver version in VERSION and config/version.yaml."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
VERSION_YAML = ROOT / "config" / "version.yaml"


def parse_version(v: str) -> tuple[int, int, int]:
    parts = v.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semver: {v}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump(v: str, part: str) -> str:
    major, minor, patch = parse_version(v)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def update_version_yaml(new_version: str, message: str) -> None:
    text = VERSION_YAML.read_text(encoding="utf-8")
    text = re.sub(r'^version:\s*".*"', f'version: "{new_version}"', text, count=1, flags=re.M)
    text = re.sub(r"^released:\s*\".*\"", f'released: "{date.today().isoformat()}"', text, count=1, flags=re.M)

    entry = (
        f'  - version: "{new_version}"\n'
        f'    date: "{date.today().isoformat()}"\n'
        f"    changes:\n"
        f'      - {message}\n'
    )
    text = text.replace("changelog:\n", f"changelog:\n{entry}", 1)
    VERSION_YAML.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump ParsLex version")
    parser.add_argument("part", choices=["patch", "minor", "major"], nargs="?", default="patch")
    parser.add_argument("-m", "--message", default="Version bump", help="Changelog entry")
    args = parser.parse_args()

    current = VERSION_FILE.read_text(encoding="utf-8").strip()
    new_version = bump(current, args.part)
    VERSION_FILE.write_text(f"{new_version}\n", encoding="utf-8")
    update_version_yaml(new_version, args.message)
    print(f"Version bumped: {current} -> {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
