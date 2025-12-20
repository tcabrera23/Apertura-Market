# 🧪 Plan de Test - Pruebas en Producción

## ✅ **Plan Test Creado Exitosamente**

Se ha agregado un nuevo plan especial para testing en producción con dinero real pero costo mínimo.

---

## 📋 **Detalles del Plan:**

| Campo | Valor |
|-------|-------|
| **ID** | `6408cac4-488b-4fd8-939c-b467f08337cf` |
| **Nombre interno** | `test` |
| **Nombre visible** | `Plan Test` |
| **Precio** | **$0.01 USD** |
| **Moneda** | USD |
| **Intervalo** | Mensual (month) |
| **Estado** | Activo ✅ |
| **Sort Order** | 999 (aparece al final) |

---

## 💰 **Costo del Testing:**

### **Con PayPal (USD):**
- Precio: **$0.01 USD**
- Comisión PayPal: ~$0.01 USD (comisión mínima)
- **Total por prueba:** ~$0.02 USD

### **Con Mercado Pago (ARS):**
- Precio: **$0.01 USD** → **~$10 ARS** (al tipo de cambio actual)
- Comisión Mercado Pago: ~$0.50 ARS
- **Total por prueba:** ~$10.50 ARS (~$0.01 USD)

---

## 🎯 **Propósito del Plan Test:**

Este plan está diseñado para:

1. ✅ **Probar el flujo completo** de suscripción en producción
2. ✅ **Verificar webhooks** de Vexor con pagos reales
3. ✅ **Validar conversión de monedas** (USD en PayPal, ARS en Mercado Pago)
4. ✅ **Confirmar actualización** de base de datos tras pago exitoso
5. ✅ **Testear cancelación** de suscripciones
6. ✅ **Probar cupones** con montos reales

**Ventajas:**
- 💵 Costo mínimo ($0.01 USD)
- 🔒 Seguro para testing
- 🚀 Resultados idénticos a planes reales
- ♻️ Reembolsable si es necesario

---

## 🎨 **Características del Plan Test:**

```json
{
  "max_rules": 3,
  "ai_assistant": true,
  "email_alerts": true,
  "telegram_alerts": false,
  "priority_support": false,
  "broker_integration": false,
  "max_watchlist_assets": 10,
  "technical_indicators": 5,
  "personalized_summaries": "general"
}
```

**Resumen:**
- ✅ Hasta 3 reglas de alertas
- ✅ Asistente de IA habilitado
- ✅ Alertas por email
- ✅ 10 activos en watchlist
- ✅ 5 indicadores técnicos
- ✅ Resúmenes personalizados generales

---

## 🧪 **Cómo Usar el Plan Test:**

### **Opción 1: Desde Pricing Page**

1. Ir a: https://bullanalytics.io/pricing.html
2. **El plan Test aparecerá automáticamente** al final de la lista
3. Hacer clic en "Comenzar Ahora" (o similar)
4. Elegir plataforma: PayPal (USD) o Mercado Pago (ARS)
5. Completar pago con tarjeta real
6. Verificar:
   - ✅ Webhook recibido en backend
   - ✅ Suscripción actualizada en Supabase
   - ✅ Plan activo en Account panel

### **Opción 2: Desde Account Panel**

1. Ir a: https://bullanalytics.io/account.html
2. Hacer clic en "Actualizar Plan"
3. **Seleccionar "Plan Test"**
4. Ver precio convertido:
   - PayPal: `$0.01/mes` (USD)
   - Mercado Pago: `~$10/mes` (ARS)
5. Elegir plataforma y completar pago
6. Verificar actualización

---

## 📊 **Cómo Aparecerá en la UI:**

### **En Pricing Page:**
```
┌─────────────────────────────────────┐
│  Plan Test                          │
│  Plan de prueba para testing...     │
│                                     │
│  $0.01/mes     (PayPal - USD)       │
│  $10/mes       (Mercado Pago - ARS) │
│                                     │
│  [Comenzar Ahora]                   │
└─────────────────────────────────────┘
```

### **En Account Panel - Modal:**
```
┌─────────────────────────────────────┐
│ Plan Free    Plan Plus    Plan Pro  │
│ Gratis       $9.99        $19.99    │
│                                     │
│ Plan Test                           │
│ $0.01  ← Seleccionado               │
└─────────────────────────────────────┘

Completar Pago:
  Plan Test
  Plan de prueba para testing...
                          $10/mes
                      ARS • ~$0.01 USD

  [PayPal (USD)]  [Mercado Pago (ARS)]
```

---

## ✅ **Checklist de Testing:**

### **Test 1: Crear Suscripción con PayPal**
- [ ] Seleccionar Plan Test
- [ ] Ver precio: `$0.01 USD`
- [ ] Clic en "Pagar con PayPal"
- [ ] Completar checkout en PayPal
- [ ] Verificar webhook recibido
- [ ] Verificar `subscriptions` tabla actualizada:
  - `status`: "active"
  - `platform`: "paypal"
  - `vexor_id`: presente
- [ ] Verificar plan activo en account.html

### **Test 2: Crear Suscripción con Mercado Pago**
- [ ] Seleccionar Plan Test
- [ ] Ver precio: `~$10 ARS` (convertido)
- [ ] Clic en "Pagar con Mercado Pago"
- [ ] Completar checkout en Mercado Pago
- [ ] Verificar webhook recibido
- [ ] Verificar `subscriptions` tabla actualizada:
  - `status`: "active"
  - `platform`: "mercadopago"
  - `vexor_id`: presente
  - `currency`: ARS
- [ ] Verificar plan activo en account.html

### **Test 3: Conversión de Monedas**
- [ ] Usuario en Argentina ve: `$10/mes (ARS)`
- [ ] Usuario en USA ve: `$0.01/mes (USD)`
- [ ] En "Completar Pago":
  - Usuario AR: `$10/mes` + `ARS • ~$0.01 USD`
  - Usuario US: `$0.01/mes` (sin conversión)

### **Test 4: Cancelación**
- [ ] Ir a account.html
- [ ] Clic en "Cancelar Suscripción"
- [ ] Confirmar cancelación
- [ ] Verificar webhook de cancelación
- [ ] Verificar `canceled_at` actualizado

### **Test 5: Cupones (Opcional)**
- [ ] Crear cupón de test: 50% descuento
- [ ] Aplicar a Plan Test
- [ ] Verificar precio: `$0.005 USD` (redondeado a $0.01)
- [ ] Completar pago

---

## 🔧 **Consultas SQL Útiles:**

### **Ver todas las suscripciones del Plan Test:**
```sql
SELECT 
    s.id,
    u.email,
    s.status,
    s.platform,
    s.vexor_id,
    s.current_period_start,
    s.current_period_end,
    s.created_at
FROM subscriptions s
JOIN user_profiles u ON s.user_id = u.id
WHERE s.plan_id = '6408cac4-488b-4fd8-939c-b467f08337cf'
ORDER BY s.created_at DESC;
```

### **Desactivar Plan Test (después de testing):**
```sql
UPDATE subscription_plans 
SET is_active = false 
WHERE name = 'test';
```

### **Reactivar Plan Test:**
```sql
UPDATE subscription_plans 
SET is_active = true 
WHERE name = 'test';
```

### **Eliminar Plan Test (cuando ya no se necesite):**
```sql
-- Solo si NO hay suscripciones activas
DELETE FROM subscription_plans 
WHERE name = 'test' 
AND id NOT IN (
    SELECT DISTINCT plan_id 
    FROM subscriptions 
    WHERE status = 'active'
);
```

---

## 💡 **Tips de Testing:**

1. **Tarjetas de Prueba (si usas modo sandbox primero):**
   - Mercado Pago: `5031 7557 3453 0604` (APRO)
   - PayPal: Cuentas generadas en PayPal Sandbox

2. **Testing en Producción:**
   - Usa tu propia tarjeta
   - El cargo será de ~$0.01-0.02 USD
   - Puedes reembolsar después desde el dashboard

3. **Webhooks:**
   - Monitorea logs en FastAPI: `/api/webhooks/vexor`
   - Verifica en Supabase Dashboard: tabla `subscriptions`
   - Logs de Edge Function: Supabase Dashboard → Functions

4. **Debugging:**
   - Abre DevTools (F12) → Consola
   - Busca logs: "Creando suscripción con:", "Respuesta de Vexor:"
   - Verifica redirección a checkout

---

## 🚨 **Importante:**

- ⚠️ Este plan es **SOLO para testing**
- ⚠️ **NO debe estar visible** para usuarios finales en producción
- ⚠️ Considera agregarlo con `sort_order = 999` para que aparezca al final
- ⚠️ O mejor aún: **desactívalo** (`is_active = false`) cuando no lo uses
- ⚠️ Puedes activarlo temporalmente solo cuando necesites hacer pruebas

---

## ✅ **Estado Actual:**

- [x] Plan Test creado en base de datos
- [x] Precio: $0.01 USD
- [x] Estado: Activo
- [x] Visible en UI automáticamente
- [ ] **Siguiente paso:** Hacer test de suscripción
- [ ] **Siguiente paso:** Verificar webhook
- [ ] **Siguiente paso:** Desactivar cuando no se use

---

**Creado:** 2025-12-20  
**ID del Plan:** `6408cac4-488b-4fd8-939c-b467f08337cf`  
**Estado:** Listo para Testing ✅

