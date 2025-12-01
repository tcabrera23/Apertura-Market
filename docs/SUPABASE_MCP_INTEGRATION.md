# 🚀 Integración de Supabase MCP con BullAnalytics

## 📋 Resumen

Este documento explica cómo utilizar el **Model Context Protocol (MCP) de Supabase** para gestionar la base de datos de BullAnalytics directamente desde el desarrollo.

## ✅ Estado Actual

### Proyecto Supabase
- **Nombre**: Bull Analytics
- **ID**: `pwumamzbicapuiqkwrey`
- **Región**: us-east-2
- **Estado**: ACTIVE_HEALTHY
- **PostgreSQL**: 17.6.1.054

### Tablas Creadas
✅ **watchlists** - Listas de seguimiento personalizadas  
✅ **watchlist_assets** - Activos dentro de cada watchlist  
✅ **alerts** - Alertas generadas por reglas  
✅ **rules** - Reglas de alertas configuradas  
✅ **subscriptions** - Suscripciones de usuarios (con `coupon_id`)  
✅ **subscription_plans** - Planes disponibles (3 planes iniciales)  
✅ **user_profiles** - Perfiles de usuario  
✅ **coupons** - Sistema de cupones de descuento  
✅ **coupon_redemptions** - Historial de redenciones  
✅ **payment_transactions** - Transacciones de PayPal  

### Políticas RLS Aplicadas
✅ Row Level Security habilitado en todas las tablas  
✅ Políticas configuradas para acceso por usuario  

## 🔧 Comandos MCP Disponibles

### Gestión de Proyectos
```javascript
// Listar proyectos
mcp_supabase_list_projects()

// Obtener detalles de un proyecto
mcp_supabase_get_project({ id: "pwumamzbicapuiqkwrey" })

// Obtener URL del proyecto
mcp_supabase_get_project_url({ project_id: "pwumamzbicapuiqkwrey" })

// Obtener anon key
mcp_supabase_get_anon_key({ project_id: "pwumamzbicapuiqkwrey" })
```

### Gestión de Base de Datos
```javascript
// Listar tablas
mcp_supabase_list_tables({ 
  project_id: "pwumamzbicapuiqkwrey",
  schemas: ["public"] 
})

// Aplicar migración
mcp_supabase_apply_migration({
  project_id: "pwumamzbicapuiqkwrey",
  name: "nombre_migracion",
  query: "CREATE TABLE ..."
})

// Ejecutar SQL (para queries, no DDL)
mcp_supabase_execute_sql({
  project_id: "pwumamzbicapuiqkwrey",
  query: "SELECT * FROM rules LIMIT 10"
})
```

### Monitoreo y Debugging
```javascript
// Obtener logs
mcp_supabase_get_logs({
  project_id: "pwumamzbicapuiqkwrey",
  service: "api" // o "postgres", "auth", "storage", etc.
})

// Obtener asesores (vulnerabilidades, performance)
mcp_supabase_get_advisors({
  project_id: "pwumamzbicapuiqkwrey",
  type: "security" // o "performance"
})
```

### Generación de Tipos
```javascript
// Generar tipos TypeScript
mcp_supabase_generate_typescript_types({
  project_id: "pwumamzbicapuiqkwrey"
})
```

## 📊 Migraciones Aplicadas

### 1. `create_watchlists_table`
Crea la tabla `watchlists` para almacenar listas de seguimiento personalizadas.

### 2. `create_watchlist_assets_table`
Crea la tabla `watchlist_assets` para los activos dentro de cada watchlist.

### 3. `create_alerts_table`
Crea la tabla `alerts` para almacenar alertas generadas.

### 4. `add_watchlists_trigger`
Agrega trigger para actualizar `updated_at` automáticamente.

### 5. `enable_rls_and_policies`
Habilita Row Level Security y crea políticas de acceso.

### 6. `create_coupons_table`
Crea la tabla `coupons` para el sistema de cupones.

### 7. `create_coupon_redemptions_table`
Crea la tabla `coupon_redemptions` para el historial de redenciones.

### 8. `add_coupon_id_to_subscriptions`
Agrega la columna `coupon_id` a la tabla `subscriptions`.

### 9. `create_payment_transactions_table`
Crea la tabla `payment_transactions` para transacciones de PayPal.

### 10. `create_validate_coupon_function`
Crea la función RPC `validate_coupon` para validar cupones.

### 11. `create_check_user_plan_limit_function`
Crea la función RPC `check_user_plan_limit` para validar límites de plan.

### 12. `enable_rls_payment_transactions`
Habilita RLS en `payment_transactions`.

### 13. `insert_initial_subscription_plans`
Inserta los 3 planes iniciales (Free, Plus, Pro).

### 14. `create_validation_triggers`
Crea triggers para validar límites automáticamente.

### 15. `create_migrate_watchlists_function`
Crea función para migrar watchlists desde JSON.

## 🔄 Migración de Datos JSON → Supabase

### Datos Actuales (JSON)
- `rules.json` → Tabla `rules`
- `watchlists.json` → Tablas `watchlists` + `watchlist_assets`
- `alerts.json` → Tabla `alerts`

### Script de Migración
```python
# migrate_data.py ya existe en el proyecto
# Ejecutar para migrar datos existentes
python migrate_data.py
```

## 🛠️ Uso en Desarrollo

### Ejemplo: Crear una nueva migración
```python
# Usando MCP desde el código
from mcp_supabase import apply_migration

result = apply_migration(
    project_id="pwumamzbicapuiqkwrey",
    name="add_new_feature",
    query="""
    ALTER TABLE public.rules 
    ADD COLUMN IF NOT EXISTS notification_preference TEXT DEFAULT 'email';
    """
)
```

### Ejemplo: Consultar datos
```python
# Ejecutar query SQL
result = execute_sql(
    project_id="pwumamzbicapuiqkwrey",
    query="""
    SELECT r.name, r.ticker, r.rule_type, u.email
    FROM public.rules r
    JOIN auth.users u ON r.user_id = u.id
    WHERE r.is_active = true
    LIMIT 10;
    """
)
```

### Ejemplo: Verificar logs
```python
# Obtener logs de errores
logs = get_logs(
    project_id="pwumamzbicapuiqkwrey",
    service="api"
)
```

## 🔐 Seguridad

### Variables de Entorno Necesarias
```bash
# .env
SUPABASE_URL=https://pwumamzbicapuiqkwrey.supabase.co
SUPABASE_SERVICE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key
```

### Notas Importantes
- ⚠️ **NUNCA** expongas el `service_role_key` en el frontend
- ✅ Usa `anon_key` en el frontend con RLS habilitado
- ✅ El MCP usa credenciales configuradas en Cursor
- ✅ Todas las tablas tienen RLS para seguridad multi-tenant

## 📈 Próximos Pasos

1. **Migrar datos existentes**: Ejecutar `migrate_data.py`
2. **Actualizar backend**: Modificar `app.py` para usar Supabase en lugar de JSON
3. **Configurar autenticación**: Integrar Supabase Auth en el frontend
4. **Aplicar migraciones faltantes**: 
   - `coupons` table
   - `coupon_redemptions` table
   - `payment_transactions` table

## 🔍 Verificación

### Verificar tablas creadas
```bash
# Usando MCP
mcp_supabase_list_tables({
  project_id: "pwumamzbicapuiqkwrey"
})
```

### Verificar políticas RLS
```sql
-- En Supabase SQL Editor
SELECT tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

## 📚 Recursos

- [Documentación Supabase MCP](https://supabase.com/docs)
- [Diseño de Base de Datos](./supabase_database_design.md)
- [Guía de Migración](./README_SUPABASE.md)

---

**Última actualización**: Diciembre 2025  
**Proyecto**: BullAnalytics  
**Estado**: ✅ Integración MCP Activa

