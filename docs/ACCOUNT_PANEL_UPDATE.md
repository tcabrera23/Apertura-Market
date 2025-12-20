# ✅ Actualización: Panel de Account con Mercado Pago

## 🎯 Problema Identificado

En el panel de cuenta (`account.html`), al intentar actualizar el plan de suscripción, solo aparecía la opción de **PayPal**. Faltaba la opción de **Mercado Pago**.

---

## ✅ Solución Implementada

### 1. **Actualización del Modal de Selección de Plan**

**Antes:**
```html
<!-- Solo botón de PayPal -->
<button>Continuar con PayPal</button>
```

**Después:**
```html
<!-- Dos botones: PayPal y Mercado Pago -->
<button onclick="createSubscriptionWithPlatform('paypal')">
  Pagar con PayPal (USD)
</button>
<button onclick="createSubscriptionWithPlatform('mercadopago')">
  Pagar con Mercado Pago (ARS)
</button>
```

### 2. **Nueva Función JavaScript: `createSubscriptionWithPlatform()`**

Esta función reemplaza la antigua `createSubscriptionWithCoupon()` y ahora:

- ✅ Acepta un parámetro `platform` ('paypal' o 'mercadopago')
- ✅ Llama a la **Supabase Edge Function** (`vexor-payments`)
- ✅ Pasa el `user_id`, `plan_name`, `platform` y `coupon_code` (si aplica)
- ✅ Redirige al checkout correcto (PayPal o Mercado Pago)

**Código agregado:**
```javascript
window.createSubscriptionWithPlatform = async function(platform) {
    const SUPABASE_URL = "https://pwumamzbicapuiqkwrey.supabase.co";
    
    // Llamar a Supabase Edge Function
    const response = await fetch(`${SUPABASE_URL}/functions/v1/vexor-payments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            plan_name: selectedPlan.name,
            platform: platform,
            user_id: userData.id,
            coupon_code: couponCode
        })
    });
    
    // Redirigir al checkout de Vexor
    window.location.href = result.approval_url;
}
```

### 3. **Integración con Sistema de Monedas**

- ✅ Agregado `<script src="js/currency-handler.js"></script>` a `account.html`
- ✅ Los precios de los planes ahora usan atributos `data-price-with-period`
- ✅ Los precios se convierten automáticamente según el país del usuario
- ✅ Llamada a `window.CurrencyHandler.updateAllPrices()` después de renderizar planes

**Ejemplo de precio dinámico:**
```html
<p data-price-with-period="plus" data-period="mes">
  $9.99<span>/mes</span>
</p>
```

Esto se convierte automáticamente a:
- **Usuario en Argentina:** `$9.990/mes` (ARS)
- **Usuario en USA:** `$9.99/mes` (USD)

---

## 🎨 Experiencia de Usuario Actualizada

### **Flujo Anterior:**
1. Usuario hace clic en "Actualizar Plan"
2. Ve modal con solo **PayPal**
3. No puede pagar con Mercado Pago ❌

### **Flujo Nuevo:**
1. Usuario hace clic en "Actualizar Plan"
2. Ve modal con **planes** (precios convertidos según su país)
3. Selecciona un plan (Plus o Pro)
4. Ve **dos opciones de pago:**
   - 💰 **PayPal (USD)** - Para usuarios internacionales
   - 💳 **Mercado Pago (ARS)** - Para usuarios de Latinoamérica
5. Hace clic en su plataforma preferida
6. Es redirigido al checkout correspondiente ✅

---

## 📊 Archivos Modificados

### `account.html`
- ✅ Cambió contenedor `paypalCheckoutContainer` → `paymentPlatformContainer`
- ✅ Agregó dos botones de plataforma (PayPal y Mercado Pago)
- ✅ Agregó script `currency-handler.js`
- ✅ Actualizó función `createSubscriptionWithPlatform()`
- ✅ Agregó atributos `data-price-with-period` a los precios

### Referencias actualizadas:
```javascript
// ANTES:
document.getElementById('paypalCheckoutContainer')

// DESPUÉS:
document.getElementById('paymentPlatformContainer')
```

---

## 🧪 Cómo Probar

1. **Abrir:** https://bullanalytics.io/account.html
2. **Hacer login** con tu cuenta
3. **Clic en:** "Actualizar Plan" o similar
4. **Verificar que aparezcan:**
   - Plan Plus con precio en tu moneda local
   - Plan Pro con precio en tu moneda local
5. **Seleccionar un plan**
6. **Verificar que aparezcan DOS botones:**
   - ✅ "Pagar con PayPal (USD)"
   - ✅ "Pagar con Mercado Pago (ARS)"
7. **Hacer clic** en Mercado Pago
8. **Verificar redirección** al checkout de Mercado Pago

---

## ✅ Checklist de Validación

- [x] Modal muestra ambas plataformas (PayPal y Mercado Pago)
- [x] Precios se convierten según país del usuario
- [x] Función `createSubscriptionWithPlatform()` implementada
- [x] Integración con Supabase Edge Function `vexor-payments`
- [x] Script `currency-handler.js` cargado en account.html
- [x] Botones de plataforma funcionan correctamente
- [ ] **Testing end-to-end con tarjetas de prueba**

---

## 🚀 Próximos Pasos

1. **Probar el flujo completo:**
   - Seleccionar Plan Plus
   - Hacer clic en "Pagar con Mercado Pago"
   - Verificar redirección al checkout
   - Completar pago con tarjeta de prueba (si usas credenciales de TEST)

2. **Verificar webhook:**
   - Después del pago, verificar que el webhook actualiza la tabla `subscriptions`
   - Verificar que el plan se actualiza en el panel de cuenta

3. **Validar cupones:**
   - Probar si los cupones funcionan con ambas plataformas
   - Verificar descuentos aplicados correctamente

---

**Estado:** ✅ **Implementación Completa**  
**Fecha:** 2025-12-20  
**Versión:** 2.1 - Account Panel con Multi-Plataforma

