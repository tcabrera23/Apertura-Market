# BullAnalytics - Documentación Técnica y Arquitectura

## 🏗️ Arquitectura del Proyecto

### Stack Tecnológico

**Backend:**
- **FastAPI** (Python): Framework web asíncrono para la API REST
- **yfinance**: Biblioteca para obtener datos financieros de Yahoo Finance
- **Groq API**: Integración con modelo LLM (Llama 3.1 8B) para agentes de IA
- **matplotlib/seaborn**: Generación de gráficos en el backend
- **cachetools**: Sistema de caché con TTL (2 minutos) para optimizar rendimiento
- **Pillow**: Procesamiento de imágenes para gráficos

**Frontend:**
- **HTML5/CSS3**: Estructura y estilos
- **Tailwind CSS**: Framework de utilidades CSS (modo oscuro con `class`)
- **JavaScript Vanilla**: Sin frameworks, código modular en archivos separados
- **Chart.js**: Librería para gráficos interactivos (actualmente solo importada, no usada - gráficos se generan en backend)

**Almacenamiento:**
- **JSON Files**: Persistencia local para:
  - `rules.json`: Reglas de alertas configuradas
  - `watchlists.json`: Listas de seguimiento personalizadas
- **localStorage**: Configuraciones de usuario (vistas de tablas, preferencias)

## 📁 Estructura de Archivos

```
finance_portfolio/
├── app.py                    # Backend FastAPI - API principal
├── requirements.txt          # Dependencias Python
├── rules.json               # Base de datos de reglas de alertas
├── watchlists.json          # Base de datos de watchlists personalizadas
│
├── index.html               # Landing page
├── dashboard.html           # Dashboard principal de activos
├── news.html                # Página de noticias financieras
├── rules.html               # Gestión de reglas de alertas
├── account.html             # Panel de cuenta/usuario
├── pricing.html             # Página de planes (integrada en index)
│
├── js/
│   ├── dashboard.js         # Lógica principal del dashboard
│   ├── analisis.js          # Gráficos y análisis visual
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

### Noticias
- `GET /api/news` - Noticias financieras (query: category)

### Reglas de Alertas
- `GET /api/rules` - Lista todas las reglas
- `POST /api/rules` - Crea nueva regla
- `PUT /api/rules/{rule_id}` - Actualiza una regla
- `DELETE /api/rules/{rule_id}` - Elimina una regla
- `POST /api/rules/chat` - Crea regla mediante IA (body: message, email)

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
5. **Nota**: Sistema de ejecución de reglas no implementado aún (pendiente)

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
    "created_at": ISO datetime
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
- **`updateTreemapChart()`**: Actualiza treemap desde imagen backend
- **`updateBarChart()`**: Actualiza gráfico de barras
- **`loadLineChart()`**: Carga gráfico de líneas histórico

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

## 🐛 Issues Conocidos / Pendientes

1. **Sistema de Ejecución de Reglas**: Las reglas se crean pero no se ejecutan automáticamente (decidir si enviar los correos mediante smtp, n8n o mediante un scheduler externo)
2. **Calendario de Resultados**: Agregar una tab de calendario de resultados en el dashboard.html
3. **Chart.js**: Importado pero no usado (gráficos se generan en backend) y no se muestran el el front (algun tipo de conflicto con la tab que se lee desde watchlist.json)
4. **Configurar vistas**: El boton esta visual en el front de dashboard.html pero no permite configurar las vistas (ocultar columnas de las tablas, cambiar el orden, filtrar)
5. **Agregar imagenes**: Cada activo debe tener su logo en la columna de assets
6. **Dark mode**: Oscurecerlo como en la imagen adjunta 
7. **Interfaz de chat de los agentes**: Debe seguir los colores principales de nuestra web (verde) y blanco o negro segun mode

## 🔄 Mejoras Futuras Sugeridas

1. **Base de Datos**: Migrar de JSON a SQLite/PostgreSQL
2. **Autenticación**: Sistema de usuarios y sesiones
3. **WebSockets**: Actualizaciones en tiempo real
4. **Testing**: Unit tests y integration tests
5. **Docker**: Containerización para deployment
6. **CI/CD**: Pipeline de deployment automatizado

---

**Última actualización**: Noviembre 2025

