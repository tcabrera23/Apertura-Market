# BullAnalytics - Supabase Migration

> Versión migrada de BullAnalytics con integración completa de Supabase PostgreSQL

## 🚀 Cambios Principales

### Migración de Almacenamiento
- ✅ **Antes**: Archivos JSON (`rules.json`, `watchlists.json`, `alerts.json`)
- ✅ **Ahora**: Supabase PostgreSQL con Row Level Security (RLS)

### Nueva Funcionalidad
- ✅ **Autenticación**: JWT tokens de Supabase Auth
- ✅ **Cupones**: Sistema completo de códigos de descuento
- ✅ **Límites de Plan**: Validación automática según suscripción
- ✅ **Tests**: Suite completa de tests unitarios e integradores

## 📋 Setup

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copia `.env.example` a `.env` y completa las credenciales:

```bash
cp .env.example .env
```

**Edita `.env`:**
```env
SUPABASE_URL=https://pwumamzbicapuiqkwrey.supabase.co
SUPABASE_SERVICE_KEY=tu_service_role_key_aqui
SUPABASE_ANON_KEY=tu_anon_key_aqui
GROQ_API_KEY=tu_groq_api_key
```

> [!IMPORTANT]
> Obtén tus credenciales en: **Supabase Dashboard → Project Settings → API**

### 3. Ejecutar SQL Schema

Ejecuta todo el SQL de `supabase_database_design.md` en el SQL Editor de Supabase:

```sql
-- Copiar y pegar desde supabase_database_design.md
-- Sección: "Script SQL Completo"
```

### 4. Ejecutar la Aplicación

```bash
# Usando el nuevo archivo con Supabase
python app_supabase.py

# O renombrar y usar app.py
mv app.py app_old.py
mv app_supabase.py app.py
python app.py
```

La aplicación estará disponible en: http://localhost:8080

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Con coverage report
pytest --cov=app_supabase --cov-report=html

# Ver el reporte en el navegador
# Abre: htmlcov/index.html
```

## 📁 Estructura de Archivos

```
finance_portfolio/
├── app_supabase.py              # ✅ Nueva aplicación con Supabase
├── app.py                       # ⚠️  Antigua aplicación (backup)
├── requirements.txt             # ✅ Actualizado con supabase, pytest
├── .env.example                 # ✅ Template de variables de entorno
├── .env                         # 🔐 Tu archivo de configuración (no commiteado)
├── pytest.ini                   # ✅ Configuración de pytest
├── tests/
│   ├── conftest.py             # ✅ Fixtures y configuración
│   ├── test_rules.py            # ✅ Tests de reglas
│   ├── test_watchlists.py       # ✅ Tests de watchlists
│   ├── test_coupons.py          # ✅ Tests de cupones
│   └── test_integration.py      # ✅ Tests de integración
├── supabase_database_design.md  # 📄 Diseño completo de DB
├── paypal_integration_guide.md  # 📄 Guía de PayPal
└── coupon_system_guide.md       # 📄 Guía de cupones
```

## 🔄 Migración de Datos

Si tienes datos en los archivos JSON antiguos:

```python
# Script manual de migración (ejecutar una sola vez)
import json
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Migrar reglas
with open('rules.json') as f:
    rules = json.load(f)
    for rule in rules:
        supabase.table("rules").insert({
            "user_id": "tu-user-id",  # Reemplazar con tu user ID
            "name": rule["name"],
            "rule_type": rule["type"],
            "ticker": rule["ticker"],
            "value_threshold": rule["value"],
            "email": rule["email"],
            "created_at": rule.get("created_at")
        }).execute()

print("✅ Migración completada")
```

## 🆕 Nuevos Endpoints

### Autenticación
Todos los endpoints ahora requieren autenticación:

```javascript
// En el frontend
const { data: { session } } = await supabase.auth.getSession();

fetch('/api/rules', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
});
```

### Cupones

```bash
# Validar cupón
POST /api/coupons/validate
{
  "code": "LAUNCH50",
  "plan_name": "plus"
}
```

### Alertas

```bash
# Obtener alertas
GET /api/alerts

# Marcar como leída
PATCH /api/alerts/{alert_id}/read
```

## 📊 Diferencias con la Versión Antigua

| Característica | Antes (JSON) | Ahora (Supabase) |
|---------------|--------------|------------------|
| **Almacenamiento** | Archivos JSON | PostgreSQL |
| **Autenticación** | ❌ No | ✅ JWT Tokens |
| **Multi-usuario** | ❌ No | ✅ Sí (RLS) |
| **Transacciones** | ❌ No | ✅ ACID |
| **Validación de límites** | ❌ Manual | ✅ Automática |
| **Cupones** | ❌ No | ✅ Sí |
| **Tests** | ❌ No | ✅ Completos |
| **Escalabilidad** | ⚠️  Limitada | ✅ Alta |

## 🔒 Seguridad

### Row Level Security (RLS)
Todas las tablas tienen políticas RLS que ensure:
- Los usuarios solo ven SUS propios datos
- No pueden modificar datos de otros usuarios
- Las operaciones admin requieren permisos especiales

### Variables de Entorno
```bash
# ❌ NUNCA commitear:
- .env
- Claves de API
- Tokens de servicio

# ✅ Commitear:
- .env.example (sin valores reales)
```

## 🐛 Troubleshooting

### Error: "SUPABASE_SERVICE_KEY not found"
- Verifica que `.env` existe y tiene las credenciales correctas
- Asegúrate de ejecutar `python app_supabase.py` desde la carpeta raíz

### Tests fallan con "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error de conexión a Supabase
- Verifica que la URL es correcta
- Verifica que el service key es válido
- Chequea tu conexión a internet

## 📚 Documentación Adicional

- [Diseño de Base de Datos](./supabase_database_design.md)
- [Guía de PayPal](./paypal_integration_guide.md)
- [Sistema de Cupones](./coupon_system_guide.md)
- [Documentación de Supabase](https://supabase.com/docs)

## 🎯 Próximos Pasos

1. ✅ Migrar datos de JSON a Supabase
2. ✅ Configurar autenticación en el frontend
3. ✅ Implement PayPal webhooks
4. ⏳ Deploy a producción
5. ⏳ Configurar CI/CD

---

**¿Preguntas?** Revisa la documentación o contacta al equipo.
