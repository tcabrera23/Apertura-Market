# Dockerfile para BullAnalytics API
FROM python:3.11-slim

# Metadatos
LABEL maintainer="BullAnalytics"
LABEL description="FastAPI application for BullAnalytics financial tracking"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para logs (si es necesario)
RUN mkdir -p /app/logs

# Exponer el puerto
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app_supabase:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

