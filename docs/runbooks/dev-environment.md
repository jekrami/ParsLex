# ParsLex Development Runbook

Short operational reference. For full step-by-step installation of all infrastructure components, see [**Technical Installation Guide**](../installation-guide.md).

## Prerequisites

- Docker Desktop (or Docker Engine + Compose)
- Python 3.12+
- Node.js 20+

## Start dev stack

```powershell
.\scripts\dev-up.ps1
```

This starts: PostgreSQL, MinIO, Redis, RabbitMQ, Qdrant, Ollama.

## Service endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | localhost:5432 | parslex / parslex |
| MinIO API | localhost:9000 | parslex / parslexsecret |
| MinIO Console | http://localhost:9001 | parslex / parslexsecret |
| Redis | localhost:6379 | — |
| RabbitMQ AMQP | localhost:5672 | parslex / parslex |
| RabbitMQ UI | http://localhost:15672 | parslex / parslex |
| Qdrant | http://localhost:6333 | — |
| Ollama | http://localhost:11434 | — |
| ParsLex API (host) | http://localhost:8010 | JWT after login |

## GPU inference (production)

For production GPU clusters, vLLM or TGI can replace Ollama. Update `config/ai/models.yaml` and `OLLAMA_BASE_URL` accordingly.

Development uses **Ollama** (`http://localhost:11434`). Pull models listed in `config/ai/models.yaml`:

```bash
ollama pull llama3.2
```

## Backup

- **PostgreSQL:** `pg_dump` daily; enable WAL archiving for PITR
- **MinIO:** bucket replication or `mc mirror` to secondary storage
- **Qdrant:** rebuild from chunk store if corrupted

## Troubleshooting

- **API cannot connect to Postgres:** Ensure `docker compose ps` shows postgres healthy
- **MinIO upload fails:** Run `storage_service.ensure_bucket()` or create bucket via console
- **CORS errors:** Verify `CORS_ORIGINS` includes frontend URL
