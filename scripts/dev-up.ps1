# Start ParsLex development infrastructure (on-prem stack)
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RootDir "deployment\docker\docker-compose.yml"
$EnvFile = Join-Path $RootDir ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item (Join-Path $RootDir ".env.example") $EnvFile
}

Write-Host "Starting ParsLex dev infrastructure..."
docker compose -f $ComposeFile up -d postgres minio redis rabbitmq qdrant ollama

Start-Sleep -Seconds 5

$version = Get-Content (Join-Path $RootDir "VERSION") -Raw

Write-Host ""
Write-Host "ParsLex dev stack is running:"
Write-Host "  PostgreSQL:     localhost:5432"
Write-Host "  MinIO API:      localhost:9000"
Write-Host "  MinIO Console:  localhost:9001  (parslex / parslexsecret)"
Write-Host "  Redis:          localhost:6379"
Write-Host "  RabbitMQ:       localhost:5672"
Write-Host "  RabbitMQ UI:    localhost:15672 (parslex / parslex)"
Write-Host "  Qdrant:         localhost:6333"
Write-Host "  Ollama:         localhost:11434"
Write-Host ""
Write-Host "Pull default model (first time):"
Write-Host "  ollama pull llama3.2"
Write-Host ""
Write-Host "Model config:     config/ai/models.yaml"
Write-Host "Platform version: $version"
