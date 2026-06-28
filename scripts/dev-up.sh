#!/usr/bin/env bash
# Start ParsLex development infrastructure (on-prem stack)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/deployment/docker/docker-compose.yml"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "Creating .env from .env.example..."
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

echo "Starting ParsLex dev infrastructure..."
docker compose -f "$COMPOSE_FILE" up -d postgres minio redis rabbitmq qdrant ollama

echo ""
echo "Waiting for services to start..."
sleep 5

echo ""
echo "ParsLex dev stack is running:"
echo "  PostgreSQL:     localhost:5432"
echo "  MinIO API:      localhost:9000"
echo "  MinIO Console:  localhost:9001  (parslex / parslexsecret)"
echo "  Redis:          localhost:6379"
echo "  RabbitMQ:       localhost:5672"
echo "  RabbitMQ UI:    localhost:15672 (parslex / parslex)"
echo "  Qdrant:         localhost:6333"
echo "  Ollama:         localhost:11434"
echo ""
echo "Pull default model (first time):"
echo "  ollama pull llama3.2"
echo ""
echo "Model config:     config/ai/models.yaml"
echo "Platform version: $(cat "$ROOT_DIR/VERSION")"
echo ""
echo "Start API:    cd backend && pip install -r requirements.txt && uvicorn apps.api.main:app --reload --app-dir ."
echo "  (run from repo root with PYTHONPATH=. or set in shell)"
echo "Start UI:     cd frontend/apps/web && npm install && npm run dev"
