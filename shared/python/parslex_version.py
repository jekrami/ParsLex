"""Load platform version from VERSION file."""

from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


@lru_cache
def get_version() -> str:
    version_file = ROOT_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"
