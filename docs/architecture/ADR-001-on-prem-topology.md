# ADR-001: On-Premise Deployment Topology

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-28 |
| **Deciders** | Architecture Team |
| **Supersedes** | — |

## Context

ParsLex is an enterprise Legal AI platform that must run **entirely on-premise** with optional air-gapped operation. Customers in regulated industries (Oil & Gas, Banking, Government) require:

- Full data residency within their network
- No dependency on public cloud AI APIs
- GPU-accelerated inference for LLM, embeddings, and OCR
- Horizontal scaling as document volume and concurrent users grow
- Enterprise security: TLS, secrets management, auditability, backup/DR

We need a deployment topology that supports a **single-node dev environment** through **multi-node production clusters** without architectural changes.

## Decision

Adopt a **layered, containerized on-prem topology** with the following tiers:

### Tier 1 — Edge & Gateway

- **Reverse proxy / API gateway** (Nginx or Traefik): TLS termination, rate limiting, static asset serving
- **Web frontend** (React SPA): served via gateway or CDN-like internal cache
- No business logic at the edge

### Tier 2 — Application Services

- **Backend API** (FastAPI): stateless, horizontally scalable
- **Worker fleet**: Celery/ARQ consumers for OCR, embedding, indexing, bulk analysis
- **Job scheduler**: optional cron/worker for compliance monitoring (future)

All application services connect to shared infrastructure via internal DNS/service discovery.

### Tier 3 — AI Inference

- **LLM inference node(s)**: vLLM or Text Generation Inference (TGI) on dedicated GPU hosts
- **Embedding service**: smaller GPU or high-CPU nodes; batch-oriented
- **OCR service**: GPU-accelerated where needed; CPU fallback for dev

AI services are **decoupled from the API tier** so GPU pools scale independently.

### Tier 4 — Data & Messaging

| Component | Role | Dev default | Prod recommendation |
|-----------|------|-------------|---------------------|
| PostgreSQL | System of record | Single instance | Primary + replica, PITR |
| MinIO | Object storage (documents, exports) | Single node | Distributed mode, erasure coding |
| Redis | Cache, sessions, job broker option | Single instance | Sentinel or cluster |
| RabbitMQ | Async job queue | Single instance | Clustered |
| Vector DB (Qdrant) | Semantic retrieval | Single instance | Replicated cluster |
| OpenSearch | Full-text search | Single node | 3-node cluster |

### Tier 5 — Observability & Security

- **Prometheus + Grafana**: metrics (API latency, queue depth, GPU utilization)
- **Loki or ELK**: centralized logs with correlation IDs
- **Vault or K8s Secrets**: credentials, JWT keys, MinIO keys
- **Backup agents**: Postgres WAL archiving, MinIO bucket replication

### Deployment modes

```text
Mode A — Docker Compose (dev / small prod)
  Single host or 2-host split (app + GPU)

Mode B — Kubernetes (recommended prod)
  Namespaces: parslex-app, parslex-ai, parslex-data
  GPU node pools via device plugin
  Helm charts per service group

Mode C — Bare metal + Compose (air-gapped)
  Offline image registry, offline model/pack update channel
```

### Network zones

```text
┌─────────────────────────────────────────────────────────┐
│ DMZ / User Network                                       │
│   Users → HTTPS → Gateway                                │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Application Zone (parslex-app)                           │
│   API, Workers, Frontend                                 │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ AI Zone (parslex-ai)                                     │
│   LLM, Embeddings, OCR                                   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Data Zone (parslex-data)                                 │
│   Postgres, MinIO, Redis, Queue, Vector, Search          │
└─────────────────────────────────────────────────────────┘
```

- AI zone has **no inbound access** from user network; only application zone may call inference APIs
- Data zone accepts connections only from application and AI zones
- Future IdP (Keycloak) integrates at gateway or API middleware layer

### GPU allocation strategy

| Workload | GPU priority | Scaling |
|----------|--------------|---------|
| LLM chat/generation | High | Dedicated GPU nodes; tensor parallel for large models |
| Embeddings (batch) | Medium | Shared pool; queue-based throttling |
| OCR | Low–Medium | Burst to GPU; CPU fallback in dev |
| Reranking (optional) | Low | CPU or small GPU |

### Environment progression

| Environment | Purpose | GPU | Data persistence |
|-------------|---------|-----|------------------|
| `dev` | Local developer | Optional mock / single GPU | Ephemeral or local volumes |
| `staging` | Integration & eval | 1 GPU node | Persistent, non-prod data |
| `prod` | Customer deployment | Production GPU pool | HA storage, backups |

Configuration is **environment-overlay based** (`config/environments/{dev,staging,prod}`) with secrets injected at runtime.

## Consequences

### Positive

- Clear separation of concerns enables independent scaling
- Air-gapped deployment is a configuration choice, not a fork
- Dev/prod parity via same container images
- GPU costs isolated to AI tier

### Negative

- Higher operational complexity than SaaS
- Customers must provision and maintain GPU hardware
- Multi-component upgrades require coordinated release notes

### Risks & mitigations

| Risk | Mitigation |
|------|------------|
| GPU node failure | Queue backpressure; graceful degradation messages in UI |
| Vector index corruption | Rebuild from chunk store in Postgres |
| Secret leakage | Vault integration; no secrets in images |
| Model update in air-gap | Signed offline bundles via admin console |

## Related ADRs

- ADR-002: Domain Pack Plugin Contract
- Future ADR-003: Authentication & IdP Federation
- Future ADR-004: Vector Database Selection
