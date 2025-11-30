# BullAnalytics - Documentación Técnica y Arquitectura

## 🏗️ Arquitectura del Proyecto

### Stack Tecnológico

**Backend:**
- **FastAPI** (Python): Framework web asíncrono para la API REST
- **yfinance**: Biblioteca para obtener datos financieros de Yahoo Finance
- **Groq API**: Integración con modelo LLM (Llama 3.1 8B) para agentes de IA
- **matplotlib/seaborn**: Generación de gráficos en el backend (imágenes PNG)
- **cachetools**: Sistema de caché con TTL (2 minutos) para optimizar rendimiento
- **Pillow**: Procesamiento de imágenes para gráficos
- **asyncio**: Tareas en background para monitoreo de reglas

**Frontend:**
- **HTML5/CSS3**: Estructura y estilos
- **Tailwind CSS**: Framework de utilidades CSS (modo oscuro con `class`)
- **JavaScript Vanilla**: Sin frameworks, código modular en archivos separados
- **Backend-Generated Images**: Gráficos renderizados como PNG en servidor

**Almacenamiento:**
- **JSON Files**: Persistencia local para:
  - `rules.json`: Reglas de alertas configuradas
  - `watchlists.json`: Listas de seguimiento personalizadas
  - `alerts.json`: Historial de alertas generadas
- **localStorage**: Configuraciones de usuario (vistas de tablas, preferencias)

## 📁 Estructura de Archivos

```
finance_portfolio/
├── app.py                    # Backend FastAPI - API principal + background tasks
├── requirements.txt          # Dependencias Python
├── rules.json               # Base de datos de reglas de alertas
├── watchlists.json          # Base de datos de watchlists personalizadas
├── alerts.json              # Historial de alertas generadas
│
├── index.html               # Landing page
├── dashboard.html           # Dashboard principal de activos
├── news.html                # Página de noticias financieras
├── rules.html               # Gestión de reglas de alertas
├── account.html             # Panel de cuenta/usuario + historial de alertas
├── pricing.html             # Página de planes (integrada en index)
│
├── js/
│   ├── dashboard.js         # Lógica principal del dashboard
│   ├── analisis.js          # Gráficos y análisis visual (backend images)
│   ├── calendar.js          # Calendario de earnings events
│   ├── table-config.js      # Configuración de vistas de tablas
│   ├── investment-chat.js   # Chat widget de inversiones (n8n)
│   ├── rules.js             # Gestión de reglas
│   ├── news.js              # Carga y renderizado de noticias
│   ├── dark-mode.js         # Toggle de modo oscuro
│   └── main.js              # Scripts generales
│
├── css/
│   ├── style.css            # Estilos globales
│   ├── dashboard.css        # Estilos específicos del dashboard
│   ├── news.css             # Estilos de noticias
│   ├── rules.css            # Estilos de reglas
│   └── pricing.css          # Estilos de pricing
│
├── images/
│   └── logo.png             # Logo de BullAnalytics
│
└── assets/
    └── mockup.jpg           # Assets de diseño
```

## 🔌 API Endpoints (FastAPI)

### Assets y Datos Financieros
- `GET /api/tracking-assets` - Activos de seguimiento popular
- `GET /api/portfolio-assets` - Activos del portafolio personal
- `GET /api/crypto-assets` - Criptomonedas
- `GET /api/argentina-assets` - Acciones argentinas
- `GET /api/asset/{ticker}` - Datos de un activo específico
- `GET /api/asset/{ticker}/history` - Historial de precios (parámetros: period, interval)
- `GET /api/search-assets` - Búsqueda de activos (query parameter)

### Watchlists Personalizadas
- `GET /api/watchlists` - Lista todas las watchlists
- `GET /api/watchlist/{name}` - Obtiene activos de una watchlist
- `POST /api/watchlist` - Crea nueva watchlist (body: name, assets[])
- `DELETE /api/watchlist/{name}` - Elimina una watchlist

### Gráficos (Retornan imágenes PNG)
- `GET /api/chart/treemap` - Treemap (parámetros: category, metric)
- `GET /api/chart/bar` - Gráfico de barras (parámetros: category, metric)
- `GET /api/chart/line` - Gráfico de líneas (parámetros: ticker, period)
- **Nota**: Todos los gráficos se generan en backend, no se usa Chart.js

### Calendario de Earnings
- `GET /api/calendar` - Próximos eventos de earnings
  - Agrega tickers de TRACKING_ASSETS, PORTFOLIO_ASSETS y watchlists
  - Filtra criptomonedas (no tienen earnings)
  - Retorna: ticker, name, date, eps_estimate, revenue_estimate
  - Solo eventos futuros/actuales

### Noticias
- `GET /api/news` - Noticias financieras (query: category)

### Reglas de Alertas
- `GET /api/rules` - Lista todas las reglas
- `POST /api/rules` - Crea nueva regla
- `PUT /api/rules/{rule_id}` - Actualiza una regla
- `DELETE /api/rules/{rule_id}` - Elimina una regla
- `POST /api/rules/chat` - Crea regla mediante IA (body: message, email)

### Sistema de Alertas
- `GET /api/alerts` - Retorna todas las alertas generadas
  - Incluye: id, rule_id, rule_name, ticker, message, timestamp, read, type

### Utilidades
- `GET /api/cache-info` - Información del estado del caché

### Servir Archivos Estáticos
- `GET /` - index.html
- `GET /dashboard.html` - Dashboard
- `GET /news.html` - Noticias
- `GET /rules.html` - Reglas
- `GET /pricing.html` - Pricing

## 🔄 Flujo de Datos

### Carga de Activos
1. Frontend solicita datos (`/api/{category}-assets`)
2. Backend verifica caché (TTLCache, 2 min TTL)
3. Si no en caché, consulta yfinance
4. Procesa datos (métricas fundamentales, técnicas, RSI, MACD, etc.)
5. Retorna JSON con AssetData
6. Frontend renderiza tabla con `renderTable()`

### Sistema de Caché
- **TTLCache**: 200 elementos máximo, 120 segundos TTL
- **Clave de caché**: `{ticker}_{cache_window}` donde cache_window = timestamp // 120
- **Ventaja**: Reduce llamadas a yfinance, mejora rendimiento

### Sistema de Ejecución de Reglas (Background Task)
1. **Inicio**: `startup_event()` inicia `check_rules_loop()` al arrancar servidor
2. **Loop Continuo**: Ejecuta cada 60 segundos
3. **Proceso**:
   - Carga todas las reglas activas desde `rules.json`
   - Obtiene tickers únicos de todas las reglas
   - Fetchea datos actuales del mercado para cada ticker
   - Evalúa cada regla contra datos actuales
   - Genera alerta si condición se cumple
   - Verifica cooldown de 24 horas por regla
   - Guarda alerta en `alerts.json`
   - Actualiza `last_triggered` en regla
4. **Tipos de Reglas Soportadas**:
   - `price_above`: Precio > valor
   - `price_below`: Precio < valor
   - `pe_above`: P/E ratio > valor
   - `pe_below`: P/E ratio < valor
   - `max_distance`: Distancia desde máximo > porcentaje
5. **Cooldown**: Previene spam, solo una alerta por regla cada 24 horas

### Generación de Gráficos
1. Frontend solicita imagen (`/api/chart/{type}`)
2. Backend genera gráfico con matplotlib/seaborn
3. Convierte a PNG en memoria (BytesIO)
4. Retorna como Response con `media_type="image/png"`
5. Frontend muestra imagen con `<img src="...">`
6. **Cache busting**: Timestamp en URL para evitar caché del navegador

### Calendario de Earnings
1. Frontend solicita `/api/calendar`
2. Backend agrega tickers de todas las categorías
3. Filtra criptomonedas (no tienen earnings)
4. Usa `yf.Tickers()` para batch fetching
5. Extrae `earningsDate`, `earningsEstimate`, `revenueEstimate`
6. Filtra solo fechas futuras/actuales
7. Retorna JSON con eventos
8. Frontend formatea y muestra en tabla

### Configuración de Tablas
1. Usuario abre modal de configuración (botón ruedita)
2. `table-config.js` carga config desde localStorage
3. Usuario modifica: columnas visibles, orden, filtros
4. Al aplicar, se guarda en localStorage
5. `applyTableConfiguration()` aplica cambios a la tabla actual

### Sistema de Reglas
1. Usuario crea regla (manual o por IA)
2. Se guarda en `rules.json`
3. Backend valida regla (tipo, ticker, valor, email)
4. Frontend muestra regla en `rules.html`
5. **Background task** monitorea regla cada 60 segundos
6. Cuando se cumple, genera alerta en `alerts.json`

### Agentes de IA

**Agente de Reglas (`/api/rules/chat`):**
- Recibe mensaje en lenguaje natural
- Usa Groq API (Llama 3.1 8B) con prompt de sistema
- Extrae: name, type, ticker, value, email
- Valida y crea regla en `rules.json`
- Retorna confirmación

**BullAgent (Investment Chat):**
- Webhook n8n: `https://dev.n8n.tomascabrera.site/webhook/.../chat`
- Payload: `{chatInput: string, sessionId: string}`
- SessionId persistido en sessionStorage
- Respuesta parseada de Markdown/HTML a HTML renderizado

## 📊 Modelos de Datos

### AssetData (Pydantic)
```python
{
    name: str,
    ticker: str,
    price: float,
    pe_ratio: Optional[float],
    all_time_high: float,
    diff_from_max: float,
    # Técnicas
    volume, market_cap, cash_flow, dividend_yield,
    year_low, year_high, avg_volume,
    rsi, macd, sma_50, sma_200,
    # Fundamentales
    revenue, revenue_growth, profit_margin,
    roe, debt_to_equity, price_to_book, beta,
    # Logo
    logo_url: Optional[str]
}
```

### Rule (JSON)
```json
{
    "id": int,
    "name": str,
    "type": "price_below" | "price_above" | "pe_below" | "pe_above" | "max_distance",
    "ticker": str,
    "value": float,
    "email": str,
    "created_at": ISO datetime,
    "last_triggered": ISO datetime | null
}
```

### Alert (JSON)
```json
{
    "id": int,
    "rule_id": int,
    "rule_name": str,
    "ticker": str,
    "message": str,
    "timestamp": ISO datetime,
    "read": bool,
    "type": "price_above" | "price_below" | "pe_above" | "pe_below" | "max_distance"
}
```

### Calendar Event (JSON)
```json
{
    "ticker": str,
    "name": str,
    "date": "YYYY-MM-DD",
    "eps_estimate": float | null,
    "revenue_estimate": float | null
}
```

### Watchlist (JSON)
```json
{
    "watchlist_name": {
        "assets": ["TICKER1", "TICKER2", ...]
    }
}
```

## 🎨 Frontend - Componentes Principales

### Dashboard (`dashboard.js`)
- **`preloadAllData()`**: Precarga todas las categorías en paralelo
- **`loadAssets(category, silent)`**: Carga datos con caché inteligente
- **`renderTable()`**: Renderiza tabla con datos
- **`createTableRow()`**: Crea fila de tabla con todas las métricas
- **`setupSorting()`**: Configura sorting en headers
- **`loadCustomWatchlists()`**: Carga y renderiza watchlists personalizadas

### Análisis (`analisis.js`)
- **`loadAnalysisData()`**: Carga datos para gráficos
- **`updateTreemapChart()`**: Carga imagen PNG desde `/api/chart/treemap` (NO Chart.js)
- **`updateBarChart()`**: Carga imagen PNG desde `/api/chart/bar` (NO Chart.js)
- **`loadLineChart()`**: Carga gráfico de líneas histórico
- **Cache busting**: Agrega `&t=${Date.now()}` a URLs de imágenes

### Calendario (`calendar.js`)
- **`loadCalendarData()`**: Fetchea datos de `/api/calendar`
- **`formatLargeNumber()`**: Formatea números grandes (B/M/K)
- **Tab activation listener**: Carga datos al hacer click en tab
- **Error handling**: Mensajes amigables para errores

### Configuración de Tablas (`table-config.js`)
- **`COLUMN_DEFINITIONS`**: Definiciones de columnas por categoría
- **`getTableConfig()`**: Obtiene/crea configuración desde localStorage
- **`applyTableConfiguration()`**: Aplica visibilidad, orden y filtros
- **`applyFilters()`**: Filtra filas según condiciones

### Chat de Inversiones (`investment-chat.js`)
- **`sendInvestmentChatMessage()`**: Envía mensaje a webhook n8n
- **`parseMarkdownToHtml()`**: Convierte markdown a HTML
- **`cleanAndStyleHtml()`**: Limpia y estiliza HTML recibido
- **`getSessionId()`**: Genera/mantiene sessionId en sessionStorage

## 🔐 Variables de Entorno

```bash
GROQ_API_KEY=tu_api_key_aqui  # Para agente de reglas
```

## 🚀 Configuración y Ejecución

### Instalación
```bash
pip install -r requirements.txt
```

### Ejecución
```bash
uvicorn app:app --reload --port 8080
```

### Acceso
- Frontend: `http://localhost:8080`
- API Docs: `http://localhost:8080/docs` (Swagger UI)

## 🔧 Configuraciones Importantes

### CORS
- Actualmente permite todos los orígenes (`*`)
- **Producción**: Restringir a dominios específicos

### Caché
- TTL: 120 segundos (2 minutos)
- Tamaño máximo: 200 elementos
- Estrategia: Por ventana de tiempo (timestamp // 120)

### Background Tasks
- **Intervalo de verificación**: 60 segundos
- **Cooldown de alertas**: 24 horas por regla
- **Inicio automático**: Al arrancar servidor via `startup_event()`

### Archivos Estáticos
- FastAPI sirve archivos estáticos desde el directorio raíz
- Rutas: `/`, `/dashboard.html`, `/news.html`, etc.

## 📝 Notas de Desarrollo

### Logos de Activos
- Se obtienen de `info.logo_url` (yfinance) o se construyen con Clearbit
- Fallback: `https://logo.clearbit.com/{domain}.com`

### Responsive Design
- Tailwind CSS con breakpoints estándar
- Chat widgets adaptativos (full-screen en mobile)
- Tablas con scroll horizontal en mobile

### Modo Oscuro
- Implementado con Tailwind `dark:` classes
- Toggle persistido en localStorage
- `dark-mode.js` maneja el toggle

### Búsqueda de Activos
- Endpoint `/api/search-assets` usa yfinance para buscar
- Debounce de 2 segundos en frontend
- Resultados mostrados en dropdown

### Gráficos
- **NO se usa Chart.js** - Todos los gráficos se generan en backend
- Imágenes PNG retornadas directamente
- Cache busting con timestamp para evitar caché del navegador

## 🐛 Issues Conocidos / Pendientes

1. **Email Notifications**: Las alertas se generan pero no se envían por email (pendiente integración SendGrid/AWS SES)
2. **Gestión de Alertas**: No hay UI para marcar alertas como leídas o eliminarlas
3. **Filtros de Calendario**: No hay capacidad de filtrar por activos específicos o rangos de fechas
4. **Notificaciones del Navegador**: No hay alertas sonoras o notificaciones del sistema
5. **Métricas de Rendimiento**: No hay estadísticas de frecuencia y precisión de reglas
6. **Account Panel**: Estructura creada pero funcionalidad limitada

## 🔄 Mejoras Futuras Sugeridas

1. **Base de Datos**: Migrar de JSON a SQLite/PostgreSQL
2. **Autenticación**: Sistema de usuarios y sesiones
3. **WebSockets**: Actualizaciones en tiempo real
4. **Email Service**: Integración con SendGrid o AWS SES
5. **Alert Management UI**: Marcar como leídas, eliminar, filtrar alertas
6. **Calendar Filters**: Filtrado por activos y rangos de fechas
7. **Browser Notifications**: Notificaciones del sistema operativo
8. **Rule Analytics**: Dashboard de métricas de rendimiento de reglas
9. **Testing**: Unit tests y integration tests
10. **Docker**: Containerización para deployment
11. **CI/CD**: Pipeline de deployment automatizado

## ✅ Funcionalidades Implementadas Recientemente

### Sistema de Ejecución de Reglas (Nov 2025)
- Background task que verifica reglas cada 60 segundos
- Generación automática de alertas cuando se cumplen condiciones
- Cooldown de 24 horas para prevenir spam
- Almacenamiento persistente en `alerts.json`
- Endpoint `/api/alerts` para consultar historial

### Calendario de Earnings (Nov 2025)
- Nueva tab "Calendario" en dashboard
- Endpoint `/api/calendar` que agrega tickers de todas las categorías
- Filtrado automático de criptomonedas
- Visualización de próximos eventos con estimaciones de EPS y revenue
- Formateo de fechas en español y números grandes (B/M/K)

### Corrección de Gráficos (Nov 2025)
- Eliminado Chart.js del frontend
- Todos los gráficos ahora se generan exclusivamente en backend
- Treemap y bar charts usan imágenes PNG del servidor
- Cache busting implementado para evitar problemas de caché

---

**Última actualización**: Noviembre 2025

