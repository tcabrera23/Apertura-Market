# 🔧 Guía de Configuración de Planes PayPal

## 📋 Resumen del Problema

Los planes en Supabase (`plus` y `pro`) necesitan tener configurado su `paypal_plan_id` para que la integración funcione.

**Estado actual:**
- ✅ Plan `free`: No necesita PayPal (gratis)
- ❌ Plan `plus`: `paypal_plan_id = NULL` (necesita configurarse)
- ❌ Plan `pro`: `paypal_plan_id = NULL` (necesita configurarse)

## 🚀 Solución: Crear Planes en PayPal

### Opción 1: Desde el Dashboard de PayPal (Recomendado)

1. **Accede a PayPal Developer Dashboard:**
   - Ve a: https://developer.paypal.com/dashboard/
   - Inicia sesión con tu cuenta de PayPal

2. **Crear Producto (si no existe):**
   - Ve a **Products** → **Create Product**
   - Tipo: **Service**
   - Nombre: `BullAnalytics Subscription`
   - Descripción: `Suscripciones mensuales de BullAnalytics`
   - Guarda el **Product ID** (ej: `PROD-XXXXX`)

3. **Crear Plan Plus:**
   - Ve a **Products** → Selecciona tu producto → **Create Plan**
   - Nombre: `BullAnalytics Plus`
   - Precio: `$9.99 USD`
   - Intervalo: `Monthly`
   - Copia el **Plan ID** (ej: `P-XXXXXXXXXX`)

4. **Crear Plan Pro:**
   - Ve a **Products** → Selecciona tu producto → **Create Plan**
   - Nombre: `BullAnalytics Pro`
   - Precio: `$19.99 USD`
   - Intervalo: `Monthly`
   - Copia el **Plan ID** (ej: `P-YYYYYYYYYY`)

5. **Actualizar Supabase:**
   
   Ejecuta el script:
   ```bash
   python update_paypal_plan_ids.py
   ```
   
   O actualiza manualmente con SQL:
   ```sql
   UPDATE subscription_plans 
   SET paypal_plan_id = 'P-XXXXXXXXXX' 
   WHERE name = 'plus';
   
   UPDATE subscription_plans 
   SET paypal_plan_id = 'P-YYYYYYYYYY' 
   WHERE name = 'pro';
   ```

### Opción 2: Usando MCP de Supabase

Si tienes los Plan IDs, puedes actualizar directamente:

```python
# Usando MCP
mcp_supabase_execute_sql(
    project_id="pwumamzbicapuiqkwrey",
    query="""
    UPDATE subscription_plans 
    SET paypal_plan_id = 'P-XXXXXXXXXX' 
    WHERE name = 'plus';
    
    UPDATE subscription_plans 
    SET paypal_plan_id = 'P-YYYYYYYYYY' 
    WHERE name = 'pro';
    """
)
```

## ✅ Verificación

Después de actualizar, verifica que los planes tengan `paypal_plan_id`:

```sql
SELECT name, display_name, price, paypal_plan_id 
FROM subscription_plans 
WHERE name IN ('plus', 'pro');
```

Deberías ver:
- `plus`: `paypal_plan_id = 'P-XXXXXXXXXX'`
- `pro`: `paypal_plan_id = 'P-YYYYYYYYYY'`

## 🔍 Troubleshooting

### Error: "Plan no configurado en PayPal"
- Verifica que `paypal_plan_id` no sea NULL en Supabase
- Asegúrate de que el Plan ID sea correcto (formato: `P-XXXXXXXXXX`)

### Error: "Error en PayPal: 404"
- Verifica que el Plan ID existe en tu cuenta de PayPal
- Asegúrate de estar usando las credenciales correctas (sandbox vs live)

### Error: "Client Authentication failed"
- Verifica que `PAYPAL_CLIENT_ID` y `PAYPAL_CLIENT_SECRET` sean correctos
- Si estás en modo `live`, usa credenciales de producción
- Si estás en modo `sandbox`, usa credenciales de sandbox

## 📝 Notas

- Los Plan IDs de PayPal son únicos y no cambian
- Una vez configurados, no necesitas volver a configurarlos
- El plan `free` no necesita `paypal_plan_id` porque es gratuito

