#!/usr/bin/env python3
"""Validate a ParsLex legal domain pack against manifest schema and structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_pack(pack_dir: Path) -> list[str]:
    errors: list[str] = []

    manifest_path = pack_dir / "manifest.yaml"
    if not manifest_path.exists():
        return [f"Missing manifest.yaml in {pack_dir}"]

    manifest = load_yaml(manifest_path)
    schema_path = pack_dir.parent.parent / "schemas" / "pack-manifest.schema.json"

    if schema_path.exists() and jsonschema is not None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(manifest, schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Manifest schema validation failed: {e.message}")

    # Check referenced files exist
    refs = [
        manifest.get("ontology_refs", {}).get("document_types"),
        manifest.get("ontology_refs", {}).get("clause_types"),
        manifest.get("ontology_refs", {}).get("obligation_types"),
        manifest.get("corpora", {}).get("regulations"),
        manifest.get("corpora", {}).get("templates"),
    ]
    for ref in refs:
        if ref and not (pack_dir / ref).exists():
            errors.append(f"Referenced file not found: {ref}")

    rules = manifest.get("rules", {})
    for key in ("compliance", "scoring"):
        ref = rules.get(key)
        if ref and not (pack_dir / ref).exists():
            errors.append(f"Rule file not found: {ref}")

    benchmarks = manifest.get("benchmarks", {})
    for key in ("qa", "analysis"):
        ref = benchmarks.get(key)
        if ref and not (pack_dir / ref).exists():
            errors.append(f"Benchmark file not found: {ref}")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate.py <pack-directory>")
        return 1

    pack_dir = Path(sys.argv[1]).resolve()
    errors = validate_pack(pack_dir)

    if errors:
        print(f"Pack validation FAILED: {pack_dir.name}")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Pack validation PASSED: {pack_dir.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
