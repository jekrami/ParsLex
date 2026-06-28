# ADR-001: On-Premise Deployment Topology

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-28 |
| **Deciders** | Architecture Team |
| **Related** | ADR-002 (Domain Pack Plugin Contract) |

## Context

ParsLex is an enterprise Legal AI platform that must run **entirely on-premise**, support **GPU-accelerated inference**, remain **air-gap capable**, and scale horizontally over a 3–5 year product horizon. The deployment model must support development, staging, and production without cloud dependencies.

Key constraints:

- All data (documents, embeddings, audit logs, models) stays within customer infrastructure
- Persian and English legal content processing
- Multi-tenant organization model with strict isolation
- Independent scaling of API tier, async workers, and GPU inference nodes

## Decision

Adopt a **layered, containerized on-prem topology** with three independently scalable planes:

1. **Control plane** — API gateway, backend services, PostgreSQL, Redis, message queue
2. **Data plane** — Object storage (MinIO), vector database, search engine
3. **AI plane** — GPU inference nodes (LLM, embeddings), OCR workers, async job consumers

### Deployment tiers

| Tier | Purpose | Components |
|------|---------|------------|
| **Dev** | Local developer workstations | Docker Compose (all services, CPU-only LLM stub) |
| **Staging** | Integration and UAT | Single-node or small K8s cluster; optional GPU |
| **Production** | Customer deployment | K8s (recommended) or bare-metal VMs with HA |

### Reference topology (production)

```
                    ┌─────────────────────────────────────┐
                    │           Load Balancer / TLS        │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │         API Gateway (Nginx/Traefik)    │
                    └──────────────────┬──────────────────┘
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
    ┌──────▼──────┐            ┌───────▼───────┐           ┌───────▼───────┐
    │  Web UI     │            │  Backend API  │           │  Admin UI     │
    │  (static)   │            │  (stateless)  │           │  (static)     │
    └─────────────┘            └───────┬───────┘           └───────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
       ┌──────▼──────┐           ┌───────▼───────┐          ┌───────▼───────┐
       │ PostgreSQL  │           │    Redis      │          │  RabbitMQ     │
       │  (primary)  │           │  (cache/sess) │          │  (job queue)  │
       └─────────────┘           └───────────────┘          └───────┬───────┘
                                                                     │
       ┌─────────────┐           ┌───────────────┐          ┌───────▼───────┐
       │   MinIO     │           │  Vector DB    │          │   Workers     │
       │  (objects)  │           │  (Qdrant)     │          │ OCR/Embed/Idx │
       └─────────────┘           └───────────────┘          └───────────────┘

       ┌─────────────────────────────────────────────────────────────────────┐
       │                    GPU Inference Cluster (AI Plane)                │
       │   vLLM / TGI (LLM)  │  Embedding Service  │  OCR (optional GPU)   │
       └─────────────────────────────────────────────────────────────────────┘
```

### Technology selections

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Container runtime | Docker + Kubernetes (prod) | Industry standard; reproducible deployments |
| RDBMS | PostgreSQL 16+ | ACID, JSONB, row-level security, pgvector option |
| Object storage | MinIO | S3-compatible; on-prem; SSE at rest |
| Cache / sessions | Redis 7 | Fast session store and job state |
| Message queue | RabbitMQ | Reliable async job delivery; dead-letter support |
| Vector DB | Qdrant | Metadata filtering; horizontal scale; on-prem |
| Search | OpenSearch (Phase 2+) | Persian analyzers; BM25 hybrid retrieval |
| LLM serving | vLLM or TGI | GPU-optimized; OpenAI-compatible API |
| Secrets | HashiCorp Vault or K8s Secrets | No credentials in images |
| Observability | Prometheus + Grafana + Loki | Metrics, dashboards, log aggregation |

### Network zones

| Zone | Access | Services |
|------|--------|----------|
| **DMZ** | External HTTPS | Load balancer, API gateway |
| **Application** | Internal only | Backend API, workers, Redis, RabbitMQ |
| **Data** | Application tier only | PostgreSQL, MinIO, Qdrant, OpenSearch |
| **AI** | Application tier only | GPU inference nodes; no direct external access |

### Scaling model

- **API tier**: Horizontal pod autoscaling based on CPU/request latency
- **Workers**: Scale by queue depth (OCR, embedding, indexing jobs)
- **GPU inference**: Dedicated node pool; model routing via AI orchestrator
- **Storage**: MinIO distributed mode; PostgreSQL read replicas for reporting

### Air-gap and updates

- Model weights and domain packs delivered as **signed offline bundles**
- Container images mirrored to customer registry
- No outbound network calls required at runtime
- Update channel: USB/secure file transfer → internal registry → rolling deploy

## Consequences

### Positive

- Full data sovereignty and regulatory compliance
- Independent scaling of compute-intensive AI workloads
- Clear security boundaries between zones
- Dev/prod parity via containerization

### Negative

- Customer bears hardware procurement and GPU capacity planning
- Higher operational burden than SaaS (backups, patching, monitoring)
- Model updates require manual or semi-automated distribution

### Mitigations

- Provide Helm charts and Docker Compose for rapid bootstrap
- Document runbooks for backup, restore, and GPU node provisioning
- LLM stub service for dev environments without GPU

## Compliance notes

- Audit logs stored in append-only PostgreSQL partition or WORM storage
- Document encryption at rest via MinIO SSE-S3
- TLS 1.3 for all inter-service communication in production
