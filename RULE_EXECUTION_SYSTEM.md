# Sistema de Ejecución Automática y Backtesting de Reglas

## 📋 Resumen

Este sistema permite:
1. **Backtesting de reglas**: Probar reglas con datos históricos antes de activarlas
2. **Ejecución automática**: Ejecutar órdenes en brokers cuando se cumplen las condiciones de las reglas
3. **Monitoreo**: Ver historial de ejecuciones y estadísticas

## 🗄️ Base de Datos

### Tablas Nuevas

1. **`rule_executions`**: Almacena todas las ejecuciones de reglas
2. **`rule_backtests`**: Almacena resultados de backtests

### Campos Nuevos en `rules`

- `execution_enabled`: Si la ejecución automática está habilitada
- `execution_type`: Tipo de ejecución (ALERT_ONLY, BUY, SELL, SIMULATION)
- `broker_connection_id`: ID de la conexión de broker a usar
- `quantity`: Cantidad a comprar/vender
- `max_execution_amount`: Monto máximo por ejecución
- `stop_loss_percent`: Stop loss porcentual (opcional)
- `take_profit_percent`: Take profit porcentual (opcional)
- `cooldown_minutes`: Minutos de espera entre ejecuciones
- `last_execution_at`: Última vez que se ejecutó

## 🚀 Instalación

### 1. Ejecutar SQL

```bash
# Ejecutar el script SQL en Supabase
psql -h your-supabase-host -U postgres -d postgres -f sql/rule_execution_system.sql
```

O ejecutar manualmente en el editor SQL de Supabase.

### 2. Instalar Dependencias

No se requieren dependencias adicionales, todo usa las existentes.

## 📡 Endpoints API

### Backtesting

#### Ejecutar Backtest
```http
POST /api/rules/{rule_id}/backtest
Authorization: Bearer {token}
Content-Type: application/json

{
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 10000
}
```

**Respuesta:**
```json
{
  "success": true,
  "backtest_id": "uuid",
  "results": {
    "total_executions": 15,
    "successful_executions": 12,
    "failed_executions": 3,
    "final_capital": 12500.50,
    "total_return": 25.00,
    "total_profit_loss": 2500.50,
    "max_drawdown": 5.2,
    "win_rate": 75.0,
    "profit_factor": 1.5,
    "sharpe_ratio": 0.8,
    "execution_details": [...],
    "daily_equity_curve": [...]
  }
}
```

#### Obtener Backtests de una Regla
```http
GET /api/rules/{rule_id}/backtests
Authorization: Bearer {token}
```

### Ejecución Automática

#### Configurar Ejecución Automática
```http
PATCH /api/rules/{rule_id}/execution-settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "execution_enabled": true,
  "execution_type": "BUY",
  "broker_connection_id": "uuid",
  "quantity": 10,
  "max_execution_amount": 1000,
  "cooldown_minutes": 60
}
```

#### Ejecutar Regla Manualmente (Testing)
```http
POST /api/rules/{rule_id}/execute
Authorization: Bearer {token}
```

#### Obtener Historial de Ejecuciones
```http
GET /api/rules/{rule_id}/executions?limit=50
Authorization: Bearer {token}
```

#### Obtener Estadísticas de Ejecución
```http
GET /api/rules/{rule_id}/execution-stats
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "total_executions": 25,
  "successful_executions": 20,
  "failed_executions": 5,
  "total_profit_loss": 1500.75,
  "avg_profit_loss": 60.03,
  "last_execution_at": "2025-12-23T10:30:00Z"
}
```

## ⚙️ Worker de Ejecución Automática

El worker verifica periódicamente las reglas activas y ejecuta órdenes cuando se cumplen.

### Ejecutar Worker

```bash
# Opción 1: Directamente
python workers/rule_executor_worker.py

# Opción 2: Como servicio (systemd)
sudo systemctl start rule-executor-worker
```

### Variables de Entorno

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
ENCRYPTION_KEY=your-encryption-key
RULE_CHECK_INTERVAL=60  # Segundos entre verificaciones
```

### Configurar como Servicio (Linux)

Crear `/etc/systemd/system/rule-executor-worker.service`:

```ini
[Unit]
Description=Rule Executor Worker
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/finance_portfolio
Environment="SUPABASE_URL=..."
Environment="SUPABASE_SERVICE_KEY=..."
Environment="ENCRYPTION_KEY=..."
Environment="RULE_CHECK_INTERVAL=60"
ExecStart=/usr/bin/python3 /path/to/finance_portfolio/workers/rule_executor_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rule-executor-worker
sudo systemctl start rule-executor-worker
```

## 🔒 Seguridad

### Límites de Riesgo

- **Cooldown**: Previene ejecuciones múltiples en corto tiempo
- **Max Execution Amount**: Limita el monto máximo por ejecución
- **Stop Loss/Take Profit**: Protección automática (futuro)

### Validaciones

- Solo usuarios premium pueden habilitar ejecución automática
- Las credenciales de broker se almacenan encriptadas
- Cada ejecución se registra para auditoría
- Verificación de cooldown antes de ejecutar

## 📊 Flujo de Trabajo

### 1. Crear y Probar Regla

1. Usuario crea una regla en `rules.html`
2. Usuario ejecuta backtest para validar la estrategia
3. Si el backtest es exitoso, habilita ejecución automática

### 2. Configurar Ejecución

1. Usuario conecta broker (IOL o Binance)
2. Configura cantidad, tipo de orden, cooldown
3. Habilita `execution_enabled`

### 3. Ejecución Automática

1. Worker verifica reglas cada 60 segundos (configurable)
2. Evalúa condiciones de cada regla
3. Si se cumple y no está en cooldown:
   - Ejecuta orden en broker
   - Registra ejecución en `rule_executions`
   - Actualiza `last_execution_at` de la regla
   - Envía notificación por email (futuro)

## 🎯 Casos de Uso

### Caso 1: Compra Automática cuando Precio Baja

```json
{
  "name": "Compra AAPL si baja de $150",
  "rule_type": "price_below",
  "ticker": "AAPL",
  "value_threshold": 150,
  "execution_enabled": true,
  "execution_type": "BUY",
  "quantity": 10,
  "cooldown_minutes": 60
}
```

### Caso 2: Venta Automática cuando P/E Sube

```json
{
  "name": "Vende META si P/E supera 40",
  "rule_type": "pe_above",
  "ticker": "META",
  "value_threshold": 40,
  "execution_enabled": true,
  "execution_type": "SELL",
  "quantity": 5,
  "cooldown_minutes": 120
}
```

## 🐛 Troubleshooting

### Worker no ejecuta reglas

1. Verificar que el worker esté corriendo: `systemctl status rule-executor-worker`
2. Verificar logs: `journalctl -u rule-executor-worker -f`
3. Verificar que las reglas tengan `execution_enabled = true`
4. Verificar que las reglas tengan broker connection configurado

### Ejecuciones fallan

1. Verificar credenciales de broker en `rule_executions.broker_response`
2. Verificar que el broker tenga fondos suficientes
3. Verificar que el ticker sea válido para el broker
4. Verificar logs del worker

### Backtest no funciona

1. Verificar que las fechas sean válidas
2. Verificar que el ticker tenga datos históricos disponibles
3. Verificar logs del servidor para errores específicos

## 📈 Próximas Mejoras

- [ ] Stop loss y take profit automáticos
- [ ] Notificaciones push/email cuando se ejecuta una orden
- [ ] Dashboard de performance de ejecuciones
- [ ] Modo simulación (paper trading) integrado
- [ ] Análisis de riesgo antes de ejecutar
- [ ] Límites diarios/semanales de ejecución
- [ ] Integración con más brokers

