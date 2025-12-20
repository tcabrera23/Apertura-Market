# 🚀 Migración a Vexor - Guía Completa y Verificación
## BullAnalytics - Sistema de Suscripciones Multi-Pasarela

---

## 📋 Resumen Ejecutivo

Has migrado exitosamente tu sistema de suscripciones de **PayPal SDK directo** a **Vexor**, permitiendo ahora:
- ✅ **PayPal** como opción de pago
- ✅ **Mercado Pago** como opción de pago
- ✅ Gestión unificada de ambos desde un único SDK
- ✅ Webhooks normalizados desde ambas plataformas

---

## 🎯 Flujo Completo del Usuario (Login → Suscripción)

### 1. **Registro de Usuario Nuevo**
```
Usuario → login.html (Sign Up) 
   ↓
FastAPI: POST /auth/signup
   ↓
Supabase Auth crea usuario en auth.users
   ↓
Trigger automático crea registro en user_profiles
   ↓
FastAPI: create_default_subscription(user_id)
   ↓
Se crea subscripción "FREE" activa permanente
   ↓
Usuario redirigido a dashboard.html con Plan FREE
```

**Código relevante:**
- `js/login.js` (líneas 136-242): Maneja el registro
- `app_supabase.py` (líneas 706-742): Crea suscripción FREE por defecto

### 2. **Upgrade desde Account.html**
```
Usuario en dashboard → clic en "Account" (navbar)
   ↓
account.html se carga
   ↓
js/account.js obtiene suscripción actual (GET /api/subscriptions/current)
   ↓
Muestra: "Plan Actual: FREE" + botón "Actualizar Plan"
   ↓
Usuario hace clic en "Actualizar Plan"
   ↓
Se abre modal con los planes (Plus $9.99, Pro $19.99)
   ↓
Usuario selecciona un plan → clic en botón del plan
   ↓
js/subscription.js: showPlatformSelector(planName)
   ↓
Modal con opciones: [PayPal] [Mercado Pago]
   ↓
Usuario elige plataforma
   ↓
createSubscription(planName, platform) →
   ↓
POST a Supabase Edge Function /functions/v1/vexor-payments
   {
     plan_name: "plus" | "pro",
     platform: "paypal" | "mercadopago",
     user_id: "uuid-del-usuario"
   }
   ↓
Edge Function consulta subscription_plans en Supabase
   ↓
Edge Function construye objeto de suscripción con:
   - price (9.99 o 19.99)
   - billing_interval ("month")
   - customer email
   ↓
Edge Function llama a vexor.subscribe.paypal() o vexor.subscribe.mercadopago()
   ↓
Vexor crea la suscripción en el proveedor elegido
   ↓
Vexor retorna payment_url (URL del checkout)
   ↓
Usuario es redirigido al checkout (PayPal o Mercado Pago)
   ↓
Usuario completa el pago
   ↓
Proveedor envía webhook a: https://api.bullanalytics.io/api/webhooks/vexor
   ↓
FastAPI: POST /api/webhooks/vexor procesa el evento
   ↓
Se actualiza/crea registro en subscriptions con:
   - status: "active"
   - vexor_id: identificador único
   - platform: "paypal" | "mercadopago"
   - current_period_start/end
   ↓
Usuario redirigido a subscription-success.html
   ↓
Usuario vuelve a account.html y ve su nuevo plan activo
```

### 3. **Upgrade Directo desde pricing.html**
```
Usuario (logueado o no) → pricing.html
   ↓
Usuario hace clic en "Comenzar Ahora" (Plan Plus o Pro)
   ↓
js/subscription.js verifica: requireAuth()
   ↓
Si NO está logueado:
   └─> Guarda la URL actual en localStorage
   └─> Redirige a login.html
   └─> Usuario se loguea/registra
   └─> Vuelve automáticamente a pricing.html
   ↓
Si está logueado:
   └─> showPlatformSelector(planName)
   └─> [Mismo flujo que en Account.html desde aquí]
```

---

## 🗂️ Arquitectura de Componentes

### **Frontend (JavaScript)**
```
js/subscription.js
├─ getAuthToken()           → Obtiene JWT del localStorage
├─ requireAuth()            → Verifica autenticación, redirige si falta
├─ showPlatformSelector()   → Modal para elegir PayPal/Mercado Pago
└─ createSubscription()     → Llama a Edge Function con plan_name + platform
```

### **Edge Function (Deno/TypeScript)**
```
supabase/functions/vexor-payments/index.ts
├─ Recibe: { plan_name, platform, user_id }
├─ Consulta: subscription_plans en Supabase
├─ Consulta: user_profiles para obtener email
├─ Construye: objeto de suscripción dinámicamente
├─ Llama: vexor.subscribe.paypal() o vexor.subscribe.mercadopago()
└─ Retorna: { success, approval_url, vexor_id }
```

### **Backend (Python FastAPI)**
```
app_supabase.py
├─ POST /auth/signup             → Registro + create_default_subscription()
├─ GET /api/subscriptions/current → Obtener suscripción activa del usuario
├─ POST /api/webhooks/vexor      → Recibe eventos de Vexor (PayPal/MercadoPago)
│   ├─ Extrae: vexor_id, event_type, platform, customData
│   ├─ Mapea: event_type → status (active/inactive/past_due)
│   ├─ Busca: subscripción existente por vexor_id
│   └─ Actualiza/Crea: registro en subscriptions
└─ [Endpoints antiguos de PayPal directo → Deprecar]
```

---

## 📊 Estructura de Datos en Supabase

### Tabla `subscription_plans`
```sql
id              | UUID    | PK
name            | TEXT    | 'free', 'plus', 'pro'
display_name    | TEXT    | 'Plan Básico', 'Plan Plus', 'Plan Pro'
description     | TEXT    | Descripción del plan
price           | DECIMAL | 0.00, 9.99, 19.99  ← ⚠️ Actualizado
billing_interval| TEXT    | 'month', 'year'
features        | JSONB   | { max_rules, max_watchlist_assets, ... }
is_active       | BOOLEAN | true
```

**✅ Verificación de Precio del Plan Pro:**
Ejecuta en SQL Editor de Supabase:
```sql
UPDATE subscription_plans 
SET price = 19.99 
WHERE name = 'pro';

-- Verificar:
SELECT name, display_name, price FROM subscription_plans;
```

**Resultado esperado:**
```
free  | Plan Básico | 0.00
plus  | Plan Plus   | 9.99
pro   | Plan Pro    | 19.99
```

### Tabla `subscriptions` (con campos de Vexor)
```sql
id                      | UUID      | PK
user_id                 | UUID      | FK → auth.users(id)
plan_id                 | UUID      | FK → subscription_plans(id)
status                  | TEXT      | 'active', 'inactive', 'past_due', 'pending_approval'
vexor_id                | TEXT      | Identificador único de Vexor
platform                | TEXT      | 'paypal' | 'mercadopago'
paypal_subscription_id  | TEXT      | (Legacy, para migración gradual)
current_period_start    | TIMESTAMP | Inicio del período actual
current_period_end      | TIMESTAMP | Fin del período actual
coupon_id               | UUID      | FK → coupons(id) (nullable)
created_at              | TIMESTAMP | 
updated_at              | TIMESTAMP |
```

---

## ⚙️ Configuraciones Necesarias

### 1. **Secrets en Supabase** (Ya configurados ✅)
```bash
VEXOR_PUBLISHABLE_KEY=pk_xxxx
VEXOR_PROJECT_ID=proj_xxxx
VEXOR_SECRET_KEY=sk_xxxx
FRONTEND_URL=https://bullanalytics.io
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
```

### 2. **Credentials en Vexor Dashboard**
Ir a: [vexorpay.com/dashboard](https://vexorpay.com/dashboard)

**Para PayPal:**
- Client ID de PayPal (sandbox o production)
- Secret de PayPal

**Para Mercado Pago:**
- Access Token de Mercado Pago (test o production)

### 3. **Webhooks en los Proveedores**

#### **PayPal:**
1. Ve a [developer.paypal.com/dashboard](https://developer.paypal.com/dashboard)
2. Tu App → **Webhooks** → **Add Endpoint**
3. URL: `https://api.bullanalytics.io/api/webhooks/vexor`
4. Eventos:
   - `BILLING.SUBSCRIPTION.CREATED`
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `PAYMENT.SALE.COMPLETED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `BILLING.SUBSCRIPTION.EXPIRED`

#### **Mercado Pago:**
1. Ve a [mercadopago.com.ar/developers/panel/app](https://www.mercadopago.com.ar/developers/panel/app)
2. Tu App → **Webhooks** → **Configurar notificaciones**
3. URL: `https://api.bullanalytics.io/api/webhooks/vexor`
4. Tópicos: `payment`, `merchant_order`

---

## 🧪 Plan de Pruebas

### Prueba 1: Usuario Nuevo (Plan FREE por defecto)
```
1. Ir a login.html
2. Registrar nueva cuenta
3. Verificar redirección a dashboard.html
4. Ir a account.html
5. ✅ Debe mostrar: "Plan Actual: Plan Básico (FREE)"
```

### Prueba 2: Upgrade desde Account (PayPal)
```
1. En account.html, clic en "Actualizar Plan"
2. Seleccionar "Plan Plus"
3. En el modal, elegir "PayPal"
4. Completar pago en sandbox de PayPal (usar tarjeta de prueba)
5. Redirige a subscription-success.html
6. Volver a account.html
7. ✅ Debe mostrar: "Plan Actual: Plan Plus ($9.99/mes)"
8. Verificar en Supabase:
   - subscriptions.status = 'active'
   - subscriptions.platform = 'paypal'
   - subscriptions.vexor_id no es NULL
```

### Prueba 3: Upgrade desde Pricing (Mercado Pago)
```
1. Cerrar sesión (logout)
2. Ir a pricing.html
3. Clic en "Conviértete en Pro"
4. Loguear o registrar
5. En el modal, elegir "Mercado Pago"
6. Completar pago en sandbox de Mercado Pago
7. Redirige a subscription-success.html
8. Ir a account.html
9. ✅ Debe mostrar: "Plan Actual: Plan Pro ($19.99/mes)"
10. Verificar en Supabase:
    - subscriptions.platform = 'mercadopago'
```

### Prueba 4: Webhook de Renovación
```
(Esto ocurre automáticamente después de 1 mes)
1. Vexor envía webhook de renovación
2. FastAPI recibe POST /api/webhooks/vexor
3. Actualiza current_period_start y current_period_end
4. ✅ Usuario sigue con acceso sin interrupciones
```

---

## 🔧 Troubleshooting Común

### Error: "Plan no encontrado en la base de datos"
**Causa:** La Edge Function no encuentra el plan en `subscription_plans`.
**Solución:**
```sql
-- Verificar que existan los planes:
SELECT * FROM subscription_plans WHERE name IN ('free', 'plus', 'pro');
```

### Error: "Usuario no encontrado"
**Causa:** El `user_id` enviado no existe en `user_profiles`.
**Solución:**
- Verificar que el usuario esté logueado correctamente.
- Revisar que `localStorage.getItem('user_data')` tenga el `id` del usuario.

### Webhook no se recibe
**Causa:** URL incorrecta o no configurada en el proveedor.
**Solución:**
1. Verificar que la URL sea exactamente: `https://api.bullanalytics.io/api/webhooks/vexor`
2. Revisar logs en FastAPI para ver si llega la petición.
3. Usar herramientas como [webhook.site](https://webhook.site) temporalmente para ver el payload.

### El usuario ve "Plan Básico" después de pagar
**Causa:** El webhook aún no se procesó o falló.
**Solución:**
1. Revisar logs de FastAPI: `POST /api/webhooks/vexor`
2. Verificar manualmente en Supabase:
```sql
SELECT * FROM subscriptions WHERE user_id = 'UUID_DEL_USUARIO' ORDER BY created_at DESC;
```
3. Si el registro no existe, ejecutar manualmente:
```sql
INSERT INTO subscriptions (user_id, plan_id, status, vexor_id, platform)
VALUES (
  'UUID_DEL_USUARIO',
  (SELECT id FROM subscription_plans WHERE name = 'plus'), -- o 'pro'
  'active',
  'identificador_de_vexor',
  'paypal' -- o 'mercadopago'
);
```

---

## 📝 Próximos Pasos Recomendados

### 1. **Limpieza de Código Legacy** (Pendiente)
Marcar como deprecados o eliminar:
- `app_supabase.py`:
  - `POST /api/subscriptions/create` (antiguo endpoint de PayPal directo)
  - `GET /api/subscriptions/verify` (verificación antigua de PayPal)
  - Función `get_paypal_access_token()` (ya no se usa)
  
**⚠️ No borrar aún:** Déjalos por 1-2 semanas por si hay usuarios en proceso de pago antiguo.

### 2. **Monitoreo y Logs**
Agregar logs más detallados en:
- Edge Function: cada paso del flujo (plan encontrado, Vexor response, etc.)
- Webhook handler: payload completo, decisiones tomadas, errores

### 3. **Manejo de Errores en Frontend**
Mejorar `js/subscription.js` para mostrar mensajes más amigables:
```javascript
catch (error) {
    // En lugar de alert(), usar un modal bonito
    showErrorModal({
        title: "Error al procesar el pago",
        message: error.message,
        action: "Reintentar"
    });
}
```

### 4. **Cancelación de Suscripciones**
Implementar botón "Cancelar Suscripción" en `account.html`:
- Crear endpoint: `POST /api/subscriptions/cancel`
- Llamar a Vexor para cancelar en el proveedor
- Actualizar `subscriptions.status = 'canceled'`

### 5. **Testing Automatizado**
Crear tests para:
- Flujo completo de registro → plan FREE
- Upgrade a Plus/Pro
- Webhook processing (mocks de payloads de PayPal/MercadoPago)

---

## 📚 Referencias

- [Documentación de Vexor](https://docs.vexorpay.com/en/docs/core/get-started/introduction)
- [Vexor Subscriptions Guide](https://docs.vexorpay.com/en/docs/core/guides/subscriptions)
- [Vexor Webhooks Guide](https://docs.vexorpay.com/en/docs/core/guides/webhooks)
- [PayPal Webhooks Events](https://developer.paypal.com/api/rest/webhooks/event-names/)
- [Mercado Pago Webhooks](https://www.mercadopago.com.ar/developers/es/docs/your-integrations/notifications/webhooks)

---

## ✅ Checklist Final

- [x] Edge Function `vexor-payments` desplegada
- [x] Tabla `subscriptions` con columnas `vexor_id` y `platform`
- [x] Frontend actualizado con selector de plataforma
- [x] Webhook endpoint `/api/webhooks/vexor` implementado
- [x] Secrets de Vexor configurados en Supabase
- [ ] **Precio del Plan Pro actualizado a $19.99 en base de datos**
- [ ] Credentials de PayPal en Vexor Dashboard
- [ ] Credentials de Mercado Pago en Vexor Dashboard
- [ ] Webhook de PayPal configurado
- [ ] Webhook de Mercado Pago configurado
- [ ] Prueba end-to-end con PayPal (sandbox)
- [ ] Prueba end-to-end con Mercado Pago (sandbox)
- [ ] Limpieza de código legacy de PayPal

---

**Documento creado**: 20 de Diciembre, 2025  
**Versión**: 1.0  
**Autor**: Migración asistida por IA

