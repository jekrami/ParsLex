# ParsLex — Enterprise Domain-Adaptive Legal AI Platform

**Version:** see [`VERSION`](VERSION) (currently **1.1.1**)

On-premise, domain-packable legal AI platform. Iranian Oil & Gas is the first knowledge domain pack.

## What's included

- **Architecture docs** — ADRs, domain pack contract, authoring guide
- **OpenAPI v1** — Identity, documents, collections, assistant, audit
- **Domain pack** — `iran-oil-gas` with ontology, rules, prompts, benchmarks
- **Phase 1 vertical slice** — Auth, document upload/storage, repository UI, audit trail
- **Ollama integration** — Parametric model config in [`config/ai/models.yaml`](config/ai/models.yaml)
- **Dev infrastructure** — PostgreSQL, MinIO, Redis, RabbitMQ, Qdrant, Ollama

## Versioning

Platform version is stored in [`VERSION`](VERSION) and [`config/version.yaml`](config/version.yaml).

```bash
# Bump version after each release-worthy change
python scripts/bump_version.py patch -m "Describe your change"
```

## Quick Start

> **Full installation:** For PostgreSQL, MinIO, Redis, RabbitMQ, Qdrant, Ollama, environment variables, verification, and troubleshooting, see the [**Technical Installation Guide**](docs/installation-guide.md).

### 1. Start infrastructure

**Windows (PowerShell):**
```powershell
.\scripts\dev-up.ps1
```

**Linux/macOS:**
```bash
chmod +x scripts/dev-up.sh
./scripts/dev-up.sh
```

### 2. Pull Ollama models

Edit [`config/ai/models.yaml`](config/ai/models.yaml) to choose models, then pull them:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text   # for Phase 2 embeddings
```

### 3. Start API

From the **repository root**:

```bash
pip install -r backend/requirements.txt
cp .env.example .env   # if not already done
set PYTHONPATH=.       # Windows: $env:PYTHONPATH="."
uvicorn backend.apps.api.main:app --reload --port 8010
```

> Note: port `8010` is used by default because port `8000` is commonly taken by
> other services (e.g. Splunk). Change it freely; if you do, update
> `VITE_API_PROXY_TARGET` for the web UI accordingly.

API: http://localhost:8010  
Docs: http://localhost:8010/docs

### 4. Start Web UI

```bash
cd frontend/apps/web
npm install
npm run dev
```

UI: http://localhost:5173

### Demo credentials

- **Email:** `admin@parslex.com`
- **Password:** `admin123`

## AI model configuration

All models are configured in [`config/ai/models.yaml`](config/ai/models.yaml):

```yaml
tasks:
  assistant:
    model: llama3.2
    temperature: 0.7
    max_tokens: 2048
```

Override connection via environment:

```env
OLLAMA_BASE_URL=http://localhost:11434
AI_MODELS_CONFIG=config/ai/models.yaml
```

## Repository Structure

```
VERSION                Platform semver (single source of truth)
config/ai/models.yaml  Parametric Ollama model profiles
docs/architecture/     ADRs and architecture decisions
contracts/openapi/     API contract
knowledge/packs/       Domain knowledge packs
backend/               FastAPI application
frontend/apps/web/     React web UI
ai/llm/                Ollama client
deployment/docker/     Docker Compose stack
tools/pack-cli/        Pack validation and benchmark tools
```

## Domain Pack

```bash
pip install pyyaml jsonschema
python tools/pack-cli/validate.py knowledge/packs/iran-oil-gas
```

## Architecture

See [ADR-001](docs/architecture/ADR-001-on-prem-topology.md) and [ADR-002](docs/architecture/ADR-002-domain-pack-plugin-contract.md).

## License

MIT
