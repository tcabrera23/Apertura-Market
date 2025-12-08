# 🚀 Optimización de Workers y Concurrencia - BullAnalytics

## Problema Identificado

Los workers se colgaban (timeout exit code 134) porque:
1. **Muchos activos**: ~27 en Portfolio + 10 en Argentina + Crypto + Tracking
2. **Llamadas síncronas**: yfinance bloquea el worker mientras espera respuesta
3. **Workers insuficientes**: Un solo worker/proceso no puede manejar tantas requests concurrentes

## Soluciones Implementadas

### 1. ⚡ Procesamiento Paralelo en Endpoints

**ANTES** (secuencial - lento):
```python
for ticker, name in PORTFOLIO_ASSETS.items():
    asset_data = get_asset_data(ticker, name)  # Bloquea aquí
    results.append(asset_data)
```

**AHORA** (paralelo - rápido):
```python
tasks = [fetch_asset_async(ticker, name) for ticker, name in PORTFOLIO_ASSETS.items()]
results = await asyncio.gather(*tasks)  # Todos en paralelo
```

**Beneficio**: 27 activos se procesan simultáneamente en lugar de secuencialmente.

### 2. 🔧 ThreadPoolExecutor Aumentado

```python
# ANTES: executor = ThreadPoolExecutor(max_workers=10)
# AHORA: executor = ThreadPoolExecutor(max_workers=30)
```

Permite 30 llamadas simultáneas a yfinance.

### 3. ⏱️ Timeouts Aumentados

```python
# ANTES: timeout=10 segundos
# AHORA: timeout=20 segundos
```

Más tiempo para que yfinance responda, especialmente con muchos activos.

### 4. 👷 Múltiples Workers Uvicorn/Gunicorn

**Configuración Recomendada**:
- **Workers**: (2 × CPU cores) + 1
- **Timeout**: 120 segundos
- **Keep-alive**: 60 segundos
- **Max Requests**: 1000 (con jitter de 50)

Para un servidor con 4 cores: **9 workers**

## 📋 Instrucciones de Deployment

### Opción A: Gunicorn + Uvicorn Workers (RECOMENDADO para producción)

```bash
# 1. Detener servicio actual
sudo systemctl stop fastapi_bullanalytics.service

# 2. Instalar gunicorn si no está instalado
pip3 install gunicorn

# 3. Copiar archivo actualizado
# (subir app_supabase.py actualizado a tu VPS)

# 4. Copiar nuevo archivo de servicio
sudo cp fastapi_bullanalytics_optimized.service /etc/systemd/system/

# 5. Recargar systemd
sudo systemctl daemon-reload

# 6. Habilitar y arrancar nuevo servicio
sudo systemctl enable fastapi_bullanalytics_optimized.service
sudo systemctl start fastapi_bullanalytics_optimized.service

# 7. Verificar estado
sudo systemctl status fastapi_bullanalytics_optimized.service

# 8. Monitorear logs
sudo journalctl -u fastapi_bullanalytics_optimized.service -f
```

### Opción B: Uvicorn Directo (más simple)

```bash
# 1. Detener servicio actual
sudo systemctl stop fastapi_bullanalytics.service

# 2. Editar el servicio existente
sudo nano /etc/systemd/system/fastapi_bullanalytics.service

# 3. Cambiar ExecStart a:
ExecStart=/usr/local/bin/uvicorn app_supabase:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 9 \
    --timeout-keep-alive 120 \
    --limit-concurrency 200

# 4. Guardar y recargar
sudo systemctl daemon-reload

# 5. Reiniciar servicio
sudo systemctl start fastapi_bullanalytics.service
```

### Opción C: Script Manual (testing)

```bash
# Hacer ejecutable
chmod +x start_api_optimized.sh

# Ejecutar
./start_api_optimized.sh
```

## 🧪 Verificación

Después de reiniciar, verifica:

1. **Workers funcionando**:
   ```bash
   ps aux | grep uvicorn
   # Deberías ver 9 procesos worker
   ```

2. **Sin timeouts**:
   ```bash
   sudo journalctl -u fastapi_bullanalytics_optimized.service | grep -i "timeout\|exit code 134"
   # No debería haber resultados recientes
   ```

3. **Endpoints respondiendo**:
   ```bash
   curl -s https://api.bullanalytics.io/api/portfolio-assets | jq length
   # Debería retornar número de activos (ej: 27)
   
   curl -s https://api.bullanalytics.io/api/argentina-assets | jq length
   # Debería retornar número de activos (ej: 10)
   ```

4. **Frontend cargando**:
   - Abrir https://bullanalytics.io/dashboard.html
   - Verificar que tabs "Acciones" y "Argentina" cargan
   - Verificar que no hay mensajes de error

## 📊 Métricas Esperadas

### ANTES (sin optimización):
- ⏱️ Tiempo respuesta: 30-60 segundos (o timeout)
- 🔴 Workers: 1-2, constantemente reiniciándose
- ❌ Errores: Worker timeout (exit code 134)
- 🐌 Frontend: Tabs no cargan o tardan mucho

### DESPUÉS (optimizado):
- ⚡ Tiempo respuesta: 5-15 segundos
- ✅ Workers: 9, estables
- ✅ Sin errores de timeout
- 🚀 Frontend: Tabs cargan rápido y correctamente

## 🔍 Troubleshooting

### Si los workers siguen muriendo:

1. **Verificar memoria**:
   ```bash
   free -h
   # Si está bajo, considera reducir workers o agregar más RAM
   ```

2. **Aumentar timeout aún más**:
   En `app_supabase.py`:
   ```python
   timeout=30  # en lugar de 20
   ```

3. **Reducir workers si RAM limitada**:
   ```bash
   # En el servicio, cambiar --workers 9 a --workers 4
   ```

4. **Verificar límites del sistema**:
   ```bash
   ulimit -a
   # Si "open files" es bajo:
   sudo nano /etc/security/limits.conf
   # Agregar:
   * soft nofile 65536
   * hard nofile 65536
   ```

### Si algunos tickers fallan:

Los logs mostrarán warnings específicos:
```bash
sudo journalctl -u fastapi_bullanalytics_optimized.service | grep -i "warning.*ticker"
```

Esto es normal y no afecta los demás activos gracias al manejo de errores individual.

## 🎯 Resumen de Cambios

| Aspecto | Antes | Ahora | Mejora |
|---------|-------|-------|--------|
| Workers | 1 | 9 | 9× capacidad |
| ThreadPool | 10 | 30 | 3× concurrencia |
| Timeout | 10s | 20s | 2× tiempo |
| Procesamiento | Secuencial | Paralelo | ~27× más rápido* |
| Keep-alive | 5s | 60s | Menos reconexiones |

*Para 27 activos en Portfolio

## ✅ Checklist de Deployment

- [ ] Backup del archivo `app_supabase.py` actual
- [ ] Subir `app_supabase.py` optimizado
- [ ] Instalar gunicorn (`pip3 install gunicorn`)
- [ ] Copiar archivo de servicio optimizado
- [ ] Recargar systemd (`daemon-reload`)
- [ ] Detener servicio antiguo
- [ ] Iniciar servicio nuevo
- [ ] Verificar workers corriendo (`ps aux | grep uvicorn`)
- [ ] Verificar logs sin errores
- [ ] Probar endpoints en curl/navegador
- [ ] Verificar frontend cargando correctamente
- [ ] Monitorear por 10-15 minutos

## 📝 Notas Adicionales

- Los cambios son **backward compatible** - si algo falla, puedes volver al archivo anterior
- El cache sigue funcionando (120 segundos), reduciendo llamadas repetidas
- Los tickers inválidos se omiten silenciosamente sin afectar los demás
- La configuración está optimizada para I/O-bound operations (llamadas a yfinance)

