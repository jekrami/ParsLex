# Domain Pack Authoring Guide

This guide explains how to create and validate Legal Domain Packs for ParsLex.

## Overview

Domain packs extend the platform with domain-specific knowledge without modifying core code. See [ADR-002](../architecture/ADR-002-domain-pack-plugin-contract.md) for the architectural contract.

## Quick start

```bash
# Validate a pack
python tools/pack-cli/validate.py knowledge/packs/iran-oil-gas

# Package for distribution
python tools/pack-cli/package.py knowledge/packs/iran-oil-gas --output dist/
```

## Pack structure

Every pack must include a `manifest.yaml` validated against `knowledge/schemas/pack-manifest.schema.json`.

Required directories:

- `ontology/` — document types, clause types, obligation types
- `regulations/inventory.yaml` — catalog of regulation corpora
- `templates/inventory.yaml` — catalog of contract templates
- `prompts/overlays/` — task-specific prompt fragments
- `rules/` — compliance and scoring rules
- `benchmarks/` — golden Q&A and analysis datasets

## Ontology guidelines

- Use stable snake_case IDs (e.g., `force_majeure`, `limitation_of_liability`)
- Provide bilingual labels (`en`, `fa`) for all user-facing types
- Clause types should map to a parent category where applicable

## Rule authoring

Compliance rules use declarative YAML. Example:

```yaml
- id: epc_liability_cap_required
  severity: high
  clause_types: [limitation_of_liability]
  condition:
    document_types: [epc_contract]
  message:
    en: "EPC contracts should include a limitation of liability clause."
    fa: "قراردادهای EPC باید شامل بند محدودیت مسئولیت باشند."
```

## Benchmarks

Each pack should ship:

- `qa-golden.json` — 50–100 question/answer pairs with expected source references
- `analysis-golden.json` — 20+ contract analysis cases with expected extractions

Benchmarks are used in CI to regression-test RAG and analysis quality per domain.

## Submission checklist

- [ ] `manifest.yaml` validates against schema
- [ ] Semver version bumped appropriately
- [ ] `min_platform_version` set correctly
- [ ] Ontology IDs are unique and documented
- [ ] Benchmarks pass locally
- [ ] No executable code in pack bundle
