#!/bin/bash

# Script optimizado para iniciar la API de BullAnalytics
# Con configuración para manejar múltiples activos

echo "🚀 Starting BullAnalytics API with optimized settings..."

# Número de CPU cores
CPU_CORES=$(nproc)
# Usar (2 x cores) + 1 como workers (buena práctica para I/O bound)
WORKERS=$((2 * CPU_CORES + 1))

echo "📊 CPU Cores: $CPU_CORES"
echo "👷 Workers: $WORKERS"
echo "⏱️  Timeout: 120s"
echo "🔗 Max Connections: 200"

# Iniciar con gunicorn + uvicorn workers (producción)
gunicorn app_supabase:app \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8080 \
    --timeout 120 \
    --keep-alive 60 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

# Alternativa con uvicorn directo (desarrollo/testing):
# uvicorn app_supabase:app \
#     --host 0.0.0.0 \
#     --port 8080 \
#     --workers $WORKERS \
#     --timeout-keep-alive 120 \
#     --limit-concurrency 200

