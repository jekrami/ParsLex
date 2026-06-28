# ParsLex — Full Technical Installation Guide

**Platform version:** see [`VERSION`](../VERSION) at repository root  
**Audience:** developers, DevOps, and solution architects deploying ParsLex on-premise

This document describes how to install and verify every infrastructure component referenced in the ParsLex architecture: **PostgreSQL**, **MinIO**, **Redis**, **RabbitMQ**, **Qdrant**, and **Ollama**, plus the **API** and **Web UI**.

For a short overview, see the [README Quick Start](../README.md).

---

## Table of contents

1. [Installation profiles](#1-installation-profiles)
2. [Prerequisites](#2-prerequisites)
3. [Port and endpoint matrix](#3-port-and-endpoint-matrix)
4. [Repository setup](#4-repository-setup)
5. [Infrastructure — Docker Compose (recommended)](#5-infrastructure--docker-compose-recommended)
6. [Service reference](#6-service-reference)
7. [Environment configuration](#7-environment-configuration)
8. [Application installation](#8-application-installation)
9. [Post-install verification](#9-post-install-verification)
10. [Ollama model setup](#10-ollama-model-setup)
11. [Domain pack validation](#11-domain-pack-validation)
12. [Running the full stack in Docker](#12-running-the-full-stack-in-docker)
13. [Troubleshooting](#13-troubleshooting)
14. [Production considerations](#14-production-considerations)

---

## 1. Installation profiles

ParsLex supports two common development setups. Choose based on what you need today.

| Profile | Infrastructure | Database | Document storage | AI | Best for |
|---------|----------------|----------|------------------|-----|----------|
| **Minimal (Phase 1)** | None required | SQLite (file) | Local filesystem | Ollama (native or Docker) | Fast UI/API iteration, no Docker |
| **Full dev stack** | Docker Compose | PostgreSQL | MinIO | Ollama (Docker or native) | Production-like integration, Phase 2+ prep |

| Component | Minimal profile | Full dev stack |
|-----------|-----------------|----------------|
| PostgreSQL | Not used | Required |
| MinIO | Not used | Required for `STORAGE_PROVIDER=minio` |
| Redis | Optional (not wired in Phase 1 API) | Started; ready for sessions/cache |
| RabbitMQ | Optional (not wired in Phase 1 API) | Started; ready for async jobs |
| Qdrant | Optional (Phase 2 embeddings) | Started; ready for vector search |
| Ollama | Required for assistant | Required for assistant |

> **Phase 1 note:** The current API uses PostgreSQL or SQLite, local or MinIO storage, and Ollama. Redis, RabbitMQ, and Qdrant are provisioned in the dev stack for upcoming pipeline features (caching, job queue, RAG indexing) but are not yet required to log in, upload documents, or use the assistant.

---

## 2. Prerequisites

### Hardware (development)

| Resource | Minimum | Recommended (with local LLM) |
|----------|---------|--------------------------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16–32 GB |
| Disk | 20 GB free | 50+ GB (models are large) |
| GPU | Optional | NVIDIA GPU with 8+ GB VRAM for faster inference |

### Software

| Tool | Version | Purpose |
|------|---------|---------|
| **Git** | 2.40+ | Clone repository |
| **Python** | 3.12+ | Backend API |
| **Node.js** | 20+ (LTS) | Frontend build/dev server |
| **npm** | 10+ | Frontend dependencies |
| **Docker Desktop** (Windows/macOS) or **Docker Engine + Compose** (Linux) | Compose v2+ | Infrastructure containers |
| **Ollama** (optional) | Latest | Native LLM serving instead of Docker Ollama |

### Windows-specific

- Enable **WSL 2** for Docker Desktop (recommended).
- Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
- If port **8000** is used by another app (e.g. Splunk), run the ParsLex API on **8010** (default in this repo).

### Linux-specific

- Add your user to the `docker` group: `sudo usermod -aG docker $USER` (log out/in after).
- For GPU-backed Ollama in Docker, install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

---

## 3. Port and endpoint matrix

Default ports when using the provided Docker Compose file (`deployment/docker/docker-compose.yml`):

| Service | Host port | Protocol | URL / connection string | Default credentials |
|---------|-----------|----------|-------------------------|---------------------|
| ParsLex API | **8010** | HTTP | `http://localhost:8010` | JWT after login |
| API docs (Swagger) | 8010 | HTTP | `http://localhost:8010/docs` | — |
| Web UI (Vite dev) | 5173 | HTTP | `http://localhost:5173` | — |
| PostgreSQL | 5432 | TCP | `postgresql://parslex:parslex@localhost:5432/parslex` | `parslex` / `parslex` |
| MinIO S3 API | 9000 | HTTP | `http://localhost:9000` | `parslex` / `parslexsecret` |
| MinIO Console | 9001 | HTTP | `http://localhost:9001` | `parslex` / `parslexsecret` |
| Redis | 6379 | TCP | `redis://localhost:6379/0` | none |
| RabbitMQ AMQP | 5672 | AMQP | `amqp://parslex:parslex@localhost:5672/` | `parslex` / `parslex` |
| RabbitMQ Management | 15672 | HTTP | `http://localhost:15672` | `parslex` / `parslex` |
| Qdrant REST | 6333 | HTTP | `http://localhost:6333` | none (dev) |
| Qdrant gRPC | 6334 | gRPC | `localhost:6334` | none (dev) |
| Ollama | 11434 | HTTP | `http://localhost:11434` | none |

Check for conflicts before starting:

```bash
# Linux / macOS
ss -tlnp | grep -E '5432|6379|8010|9000|11434|6333'

# Windows PowerShell
Get-NetTCPConnection -State Listen | Where-Object LocalPort -in 5432,6379,8010,9000,11434,6333
```

---

## 4. Repository setup

```bash
git clone https://github.com/<your-org>/ParsLex.git
cd ParsLex
```

Create environment file from the template:

```bash
# Linux / macOS
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` for your chosen profile (see [Section 7](#7-environment-configuration)).

---

## 5. Infrastructure — Docker Compose

The canonical stack definition lives at [`deployment/docker/docker-compose.yml`](../deployment/docker/docker-compose.yml).

### 5.1 Start all infrastructure services

**Windows (PowerShell):**

```powershell
.\scripts\dev-up.ps1
```

**Linux / macOS:**

```bash
chmod +x scripts/dev-up.sh
./scripts/dev-up.sh
```

These scripts:

1. Copy `.env.example` → `.env` if missing.
2. Start: `postgres`, `minio`, `redis`, `rabbitmq`, `qdrant`, `ollama`.
3. Print connection endpoints and the current platform version.

Equivalent manual command:

```bash
docker compose -f deployment/docker/docker-compose.yml up -d postgres minio redis rabbitmq qdrant ollama
```

### 5.2 Check container health

```bash
docker compose -f deployment/docker/docker-compose.yml ps
```

Wait until PostgreSQL and Redis show **healthy**. Example:

```
NAME               STATUS
parslex-postgres   Up (healthy)
parslex-redis      Up (healthy)
parslex-minio      Up
parslex-rabbitmq   Up (healthy)
parslex-qdrant     Up
parslex-ollama     Up
```

### 5.3 Stop infrastructure

```bash
docker compose -f deployment/docker/docker-compose.yml down
```

Data persists in named Docker volumes (`parslex-postgres-data`, `parslex-minio-data`, etc.).

To remove data volumes (destructive):

```bash
docker compose -f deployment/docker/docker-compose.yml down -v
```

### 5.4 Persistent volumes

| Volume | Mount point in container | Contents |
|--------|--------------------------|----------|
| `parslex-postgres-data` | `/var/lib/postgresql/data` | Database files |
| `parslex-minio-data` | `/data` | Uploaded documents (S3 objects) |
| `parslex-redis-data` | `/data` | Redis AOF/RDB |
| `parslex-rabbitmq-data` | `/var/lib/rabbitmq` | Queues, definitions |
| `parslex-qdrant-data` | `/qdrant/storage` | Vector collections |
| `parslex-ollama-data` | `/root/.ollama` | Downloaded models |

---

## 6. Service reference

### 6.1 PostgreSQL

**Role:** Primary relational store for users, organizations, documents metadata, audit events, and AI sessions.

**Image:** `postgres:16-alpine`  
**Connection (from host):**

```
postgresql://parslex:parslex@localhost:5432/parslex
```

**Verify:**

```bash
docker exec parslex-postgres pg_isready -U parslex
```

**Connect with psql:**

```bash
docker exec -it parslex-postgres psql -U parslex -d parslex
```

**Backup (dev):**

```bash
docker exec parslex-postgres pg_dump -U parslex parslex > parslex_backup.sql
```

**Restore:**

```bash
cat parslex_backup.sql | docker exec -i parslex-postgres psql -U parslex -d parslex
```

When using PostgreSQL, set in `.env`:

```env
DATABASE_URL=postgresql://parslex:parslex@localhost:5432/parslex
```

Tables are created automatically on first API startup (SQLAlchemy `create_all`).

---

### 6.2 MinIO

**Role:** S3-compatible object storage for document binaries (PDF, DOCX, etc.).

**Image:** `minio/minio:latest`  
**API:** `http://localhost:9000`  
**Web console:** `http://localhost:9001` — login `parslex` / `parslexsecret`

**Verify API:**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live
# Expect: 200
```

**Enable MinIO in the API** (`.env`):

```env
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=parslex
MINIO_SECRET_KEY=parslexsecret
MINIO_BUCKET=parslex-documents
MINIO_SECURE=false
```

The API creates the bucket `parslex-documents` on first upload if it does not exist.

**Browse objects:** Open MinIO Console → Buckets → `parslex-documents`. Keys follow `{org_id}/{uuid}/{filename}`.

**Install MinIO Client (`mc`) — optional:**

```bash
mc alias set parslex http://localhost:9000 parslex parslexsecret
mc ls parslex/parslex-documents
```

---

### 6.3 Redis

**Role:** Session cache, rate limiting, and pub/sub (planned for job status and real-time features).

**Image:** `redis:7-alpine`  
**URL:** `redis://localhost:6379/0`

**Verify:**

```bash
docker exec parslex-redis redis-cli ping
# PONG
```

**Environment:**

```env
REDIS_URL=redis://localhost:6379/0
```

**Monitor (debug):**

```bash
docker exec -it parslex-redis redis-cli MONITOR
```

---

### 6.4 RabbitMQ

**Role:** Async job orchestration — document ingestion, OCR, chunking, embedding pipelines (Phase 2+).

**Image:** `rabbitmq:3-management-alpine`  
**AMQP:** `localhost:5672`  
**Management UI:** `http://localhost:15672` — login `parslex` / `parslex`

**Verify:**

```bash
docker exec parslex-rabbitmq rabbitmq-diagnostics -q ping
```

**Planned connection string (when workers are added):**

```
amqp://parslex:parslex@localhost:5672/
```

From the management UI you can inspect queues, exchanges, and message rates once ingestion workers are deployed.

---

### 6.5 Qdrant

**Role:** Vector database for semantic search and RAG retrieval over legal document chunks.

**Image:** `qdrant/qdrant:v1.12.5`  
**REST API:** `http://localhost:6333`  
**Dashboard:** `http://localhost:6333/dashboard`

**Verify:**

```bash
curl http://localhost:6333/healthz
# {"title":"qdrant - vectorass...","version":"..."}
```

**List collections (empty until indexing runs):**

```bash
curl http://localhost:6333/collections
```

**gRPC** (for high-throughput clients): `localhost:6334`

Phase 2 will create collections per organization or domain pack. No API configuration is required in Phase 1 beyond having the service running.

---

### 6.6 Ollama

**Role:** On-premise LLM inference and embeddings. Model names and parameters are driven by [`config/ai/models.yaml`](../config/ai/models.yaml).

#### Option A — Ollama in Docker (started by `dev-up`)

**URL:** `http://localhost:11434`

```bash
curl http://localhost:11434/api/tags
```

Pull models into the container volume:

```bash
docker exec -it parslex-ollama ollama pull llama3.2
docker exec -it parslex-ollama ollama pull nomic-embed-text
```

#### Option B — Ollama installed natively (recommended on Windows with GPU)

1. Download from [https://ollama.com/download](https://ollama.com/download).
2. Install and ensure the service listens on `11434`.
3. Pull models on the host:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

4. If using Docker for other services but native Ollama, keep:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

If **only** Docker Ollama is used, the URL is the same from the host. Inside the API container, Compose sets `http://ollama:11434`.

#### GPU support (Docker Ollama)

Uncomment the `deploy.resources.reservations.devices` section in `docker-compose.yml` for NVIDIA GPU passthrough. Requires NVIDIA drivers and Container Toolkit.

#### Test chat

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}'
```

---

## 7. Environment configuration

Complete `.env` reference for local development:

```env
# --- Application ---
SECRET_KEY=dev-secret-change-in-production
DEBUG=true

# --- Database ---
# Full stack:
DATABASE_URL=postgresql://parslex:parslex@localhost:5432/parslex
# Minimal profile (no PostgreSQL):
# DATABASE_URL=sqlite:///./parslex_dev.db

# --- Document storage ---
# Minimal profile:
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=storage/documents
# Full stack with MinIO:
# STORAGE_PROVIDER=minio
# MINIO_ENDPOINT=localhost:9000
# MINIO_ACCESS_KEY=parslex
# MINIO_SECRET_KEY=parslexsecret
# MINIO_BUCKET=parslex-documents
# MINIO_SECURE=false

# --- Cache ---
REDIS_URL=redis://localhost:6379/0

# --- AI / Ollama ---
AI_MODELS_CONFIG=config/ai/models.yaml
OLLAMA_BASE_URL=http://localhost:11434

# --- CORS (must include your UI origin) ---
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# --- Seeded admin user (first boot only) ---
DEFAULT_ADMIN_EMAIL=admin@parslex.com
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_NAME=Platform Admin
```

### Profile presets

**Minimal — no Docker:**

```env
DATABASE_URL=sqlite:///./parslex_dev.db
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=storage/documents
OLLAMA_BASE_URL=http://localhost:11434
```

**Full dev stack — infrastructure in Docker, API on host:**

```env
DATABASE_URL=postgresql://parslex:parslex@localhost:5432/parslex
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=parslex
MINIO_SECRET_KEY=parslexsecret
MINIO_BUCKET=parslex-documents
MINIO_SECURE=false
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 8. Application installation

### 8.1 Python virtual environment

From the repository root:

```bash
# Linux / macOS
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Development extras (tests):

```bash
pip install -r backend/requirements-dev.txt
```

### 8.2 Start the API

The API must resolve the `apps` package. Run from the `backend` directory **or** set `PYTHONPATH` to the repo root.

**Recommended (from `backend/`):**

```bash
cd backend
uvicorn apps.api.main:app --reload --port 8010
```

**Alternative (from repo root):**

```bash
# Linux / macOS
export PYTHONPATH=backend
uvicorn apps.api.main:app --reload --port 8010 --app-dir backend

# Windows PowerShell
$env:PYTHONPATH = "backend"
uvicorn apps.api.main:app --reload --port 8010 --app-dir backend
```

On first start the API will:

- Create database tables (PostgreSQL or SQLite).
- Seed the default admin user if no users exist.

**Default login:**

| Field | Value |
|-------|-------|
| Email | `admin@parslex.com` |
| Password | `admin123` |

### 8.3 Start the Web UI

```bash
cd frontend/apps/web
npm install
npm run dev
```

Open **http://localhost:5173**.

The Vite dev server proxies `/api` to `http://localhost:8010` by default. Override:

```bash
# Linux / macOS
VITE_API_PROXY_TARGET=http://localhost:8010 npm run dev

# Windows PowerShell
$env:VITE_API_PROXY_TARGET = "http://localhost:8010"
npm run dev
```

### 8.4 Run API tests

```bash
cd backend
pytest tests/ -v
```

Tests use in-memory SQLite and do not require Docker services.

---

## 9. Post-install verification

Run these checks after installation. Order matters: infrastructure first, then API, then UI.

### 9.1 Infrastructure checklist

| Step | Command | Expected |
|------|---------|----------|
| PostgreSQL | `docker exec parslex-postgres pg_isready -U parslex` | `accepting connections` |
| MinIO | `curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live` | `200` |
| Redis | `docker exec parslex-redis redis-cli ping` | `PONG` |
| RabbitMQ | `docker exec parslex-rabbitmq rabbitmq-diagnostics -q ping` | `Ping succeeded` |
| Qdrant | `curl http://localhost:6333/healthz` | JSON with version |
| Ollama | `curl http://localhost:11434/api/tags` | JSON listing models |

### 9.2 API health

```bash
curl http://localhost:8010/health
```

Example response:

```json
{
  "status": "ok",
  "version": "1.1.1",
  "ai": {
    "status": "ok",
    "provider": "ollama",
    "models_available": ["llama3.2", "..."]
  }
}
```

If `ai.status` is not `ok`, verify Ollama is running and at least one model from `config/ai/models.yaml` is pulled.

### 9.3 Authentication

```bash
curl -s -X POST http://localhost:8010/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@parslex.com","password":"admin123"}'
```

Expect `access_token` in the JSON body.

### 9.4 Document upload (UI or API)

1. Log in at http://localhost:5173.
2. Upload a PDF or document.
3. Confirm it appears in the repository list.

With **local storage**, files land under `storage/documents/`.  
With **MinIO**, confirm in the console under bucket `parslex-documents`.

### 9.5 Assistant (optional)

From the UI or via `/api/v1/.../assistant` endpoints after models are pulled. Requires Ollama and a chat model (default: `llama3.2`).

---

## 10. Ollama model setup

Models are configured per task in [`config/ai/models.yaml`](../config/ai/models.yaml):

| Task | Default model | Purpose |
|------|---------------|---------|
| `assistant` | `llama3.2` | Legal Q&A chat |
| `summarization` | `llama3.2` | Document summaries |
| `embedding` | `nomic-embed-text` | Vector embeddings (Phase 2) |
| `compliance_check` | `llama3.2` | Compliance analysis |

**Pull required models:**

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

**Change models** — edit `config/ai/models.yaml`, then pull the new model name. No API restart required for task routing (config is read per request via the LLM service).

**Persian / bilingual workloads:** Consider larger multilingual models (e.g. `aya-expanse:8b`, domain-specific fine-tunes). Update `tasks.assistant.model` accordingly.

**Override Ollama URL** without editing YAML:

```env
OLLAMA_BASE_URL=http://192.168.1.50:11434
```

---

## 11. Domain pack validation

Validate the bundled Iranian Oil & Gas domain pack:

```bash
pip install pyyaml jsonschema
python tools/pack-cli/validate.py knowledge/packs/iran-oil-gas
```

Regenerate benchmark fixtures:

```bash
python tools/pack-cli/generate_benchmarks.py
```

---

## 12. Running the full stack in Docker

To run the **API inside Docker** as well (not only infrastructure):

1. Ensure `.env` exists at repo root.
2. Build and start the API service:

```bash
docker compose -f deployment/docker/docker-compose.yml up -d --build api
```

The API container listens on host port **8010** (mapped to container port 8000). Environment variables inside the container point to Docker service hostnames (`postgres`, `minio`, `ollama`, etc.).

Start infrastructure + API:

```bash
docker compose -f deployment/docker/docker-compose.yml up -d
```

The Web UI is still run locally with `npm run dev` unless you add a frontend container in a future release.

---

## 13. Troubleshooting

### Port 8010 / 8000 already in use

Another process may be bound to the port. On Windows, Splunk often uses **8000**.

```powershell
Get-NetTCPConnection -LocalPort 8010 -State Listen
```

Use a different port: `uvicorn apps.api.main:app --port 8020` and set `VITE_API_PROXY_TARGET=http://localhost:8020`.

### Document upload returns 500 (connection refused to port 9000)

**Cause:** `STORAGE_PROVIDER=minio` but MinIO is not running.  
**Fix:** Start MinIO (`.\scripts\dev-up.ps1`) **or** switch to local storage:

```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=storage/documents
```

Restart the API after changing `.env`.

### API cannot connect to PostgreSQL

1. `docker compose -f deployment/docker/docker-compose.yml ps` — postgres must be **healthy**.
2. Confirm `DATABASE_URL` uses `localhost:5432` when API runs on host.
3. When API runs in Docker, use `postgresql://parslex:parslex@postgres:5432/parslex` (set by Compose).

### `uvicorn` not found

Activate the virtual environment and install dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### bcrypt / login errors

Ensure `bcrypt` is pinned as in `requirements.txt` (`bcrypt>=4.0,<4.1`). Reinstall: `pip install -r backend/requirements.txt --force-reinstall`.

### Ollama health check fails

- Confirm Ollama is running: `curl http://localhost:11434/api/tags`
- Pull the model named in `config/ai/models.yaml`
- If Ollama runs in Docker but you use host CLI, pull via `docker exec parslex-ollama ollama pull llama3.2`

### CORS errors in browser

Add your frontend origin to `.env`:

```env
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Restart the API.

### MinIO bucket missing

The API auto-creates `parslex-documents` on upload. Manually via console: Buckets → Create Bucket → `parslex-documents`.

### Docker volumes full / corrupt

Reset a single service (example — PostgreSQL, **destroys data**):

```bash
docker compose -f deployment/docker/docker-compose.yml stop postgres
docker volume rm parslex-postgres-data
docker compose -f deployment/docker/docker-compose.yml up -d postgres
```

### WSL2 / Docker Desktop slow on Windows

- Store the repo on the WSL filesystem (`\\wsl$\...`) for better I/O.
- Allocate sufficient memory to Docker Desktop (Settings → Resources).

---

## 14. Production considerations

This guide targets **development**. For production deployments, refer to [ADR-001 — On-Prem Topology](architecture/ADR-001-on-prem-topology.md):

- Replace default passwords and `SECRET_KEY`.
- Use Kubernetes or hardened bare-metal layout with network zones.
- Enable TLS at the ingress/gateway.
- Use managed backups for PostgreSQL and MinIO replication.
- Prefer dedicated GPU nodes for Ollama or migrate to vLLM/TGI for scale.
- Enable Qdrant authentication and TLS in non-trusted networks.
- Restrict RabbitMQ and Redis to internal networks only.

---

## Quick reference — start order

1. `.\scripts\dev-up.ps1` or `./scripts/dev-up.sh` — infrastructure  
2. `ollama pull llama3.2` (and models from `config/ai/models.yaml`)  
3. Configure `.env` for your profile  
4. `pip install -r backend/requirements.txt` → start API on port **8010**  
5. `npm install && npm run dev` in `frontend/apps/web`  
6. Open http://localhost:5173 — login `admin@parslex.com` / `admin123`  
7. Run verification steps in [Section 9](#9-post-install-verification)

---

## Related documentation

- [ADR-001 — On-Prem Topology](architecture/ADR-001-on-prem-topology.md)
- [ADR-002 — Domain Pack Plugin Contract](architecture/ADR-002-domain-pack-plugin-contract.md)
- [Domain Pack Authoring Guide](domain-packs/pack-authoring-guide.md)
- [Development Runbook](runbooks/dev-environment.md)
- [OpenAPI Specification](../contracts/openapi/parslex-v0.yaml)
