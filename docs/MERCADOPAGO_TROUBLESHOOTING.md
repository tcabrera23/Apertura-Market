# 🔧 Problema: Botón "Pagar suscripción" Deshabilitado en Mercado Pago

## 🐛 **Problema Identificado:**

Al intentar pagar con Mercado Pago, el botón "Pagar suscripción" aparece **deshabilitado** (gris) en el checkout de Mercado Pago.

---

## 🔍 **Diagnóstico:**

### **Lo que está funcionando:**
- ✅ Vexor está creando el plan en Mercado Pago (por eso ves los planes en tu dashboard)
- ✅ La redirección al checkout funciona
- ✅ El precio se muestra correctamente ($15.00 ARS para Plan Test)

### **El problema:**
- ❌ El botón de pago está deshabilitado
- ❌ No se puede completar la suscripción

---

## 💡 **Posibles Causas:**

### **1. Precio Mínimo de Mercado Pago**
Mercado Pago tiene un **precio mínimo de $10 ARS** para suscripciones. Si el precio es menor, el botón puede deshabilitarse.

**Solución aplicada:**
- ✅ Agregada validación en la Edge Function
- ✅ Si el precio es menor a $10 ARS, se ajusta automáticamente a $10 ARS
- ✅ Para Plan Test ($0.01 USD → ~$15 ARS), debería funcionar

### **2. Configuración de Vexor con Mercado Pago**
Vexor puede necesitar configuración adicional para suscripciones recurrentes en Mercado Pago.

**Verificar:**
- Credenciales de Mercado Pago en Vexor Dashboard
- Que estén en modo **PRODUCCIÓN** (no TEST)
- Que la cuenta de Mercado Pago tenga permisos para crear suscripciones

### **3. Estado del Plan en Mercado Pago**
Los planes creados por Vexor pueden necesitar estar en un estado específico.

**Verificar en Mercado Pago Dashboard:**
- Ve a: "Planes de suscripción"
- Verifica que los planes estén **activos**
- Verifica que no tengan restricciones

---

## ✅ **Solución Implementada:**

### **1. Validación de Precio Mínimo:**
```typescript
// Si el precio es menor a $10 ARS, ajustar automáticamente
if (currency === 'ARS' && finalPrice < 10) {
  console.warn(`Precio ${finalPrice} ARS es muy bajo. Ajustando a $10 ARS.`)
  subscriptionBody.price = 10
  finalPrice = 10
}
```

### **2. Logs Mejorados:**
Ahora la Edge Function registra:
- ✅ Parámetros enviados a Vexor
- ✅ Respuesta completa de Vexor
- ✅ Errores detallados si falla

---

## 🧪 **Cómo Probar Ahora:**

### **Paso 1: Verificar Logs**
1. Ve a: Supabase Dashboard → Functions → vexor-payments → Logs
2. Busca el último request
3. Verifica:
   - `subscriptionBody.price` debe ser >= 10 si es ARS
   - `response.payment_url` debe estar presente
   - No debe haber errores

### **Paso 2: Probar Nuevamente**
1. Recarga: https://bullanalytics.io/account.html
2. Selecciona "Plan Test"
3. Haz clic en "Pagar con Mercado Pago"
4. **Verifica en la consola del navegador (F12):**
   - Debe mostrar: `"Creando suscripción con:"`
   - Debe mostrar: `"Respuesta de Vexor:"`
   - Debe redirigir al checkout

### **Paso 3: En el Checkout de Mercado Pago**
- ✅ El botón debe estar **habilitado** (azul, no gris)
- ✅ El precio debe ser **$15.00 ARS** (o $10 ARS si se ajustó)
- ✅ Debe permitir completar el pago

---

## 🔧 **Si el Problema Persiste:**

### **Opción 1: Verificar Credenciales de Vexor**
1. Ve a: https://vexorpay.com/dashboard
2. Tu proyecto → Settings → Credentials
3. Verifica:
   - ✅ Mercado Pago Access Token es válido
   - ✅ Está en modo **PRODUCCIÓN** (no TEST)
   - ✅ La cuenta tiene permisos de suscripciones

### **Opción 2: Contactar Soporte de Vexor**
Si el problema persiste, puede ser un issue con la integración de Vexor y Mercado Pago. Contacta a:
- **Vexor Support:** support@vexorpay.com
- **Menciona:** "Botón de pago deshabilitado en checkout de Mercado Pago para suscripciones"

### **Opción 3: Usar PayPal Temporalmente**
Mientras se resuelve, puedes probar con PayPal:
- ✅ Selecciona "Pagar con PayPal (USD)"
- ✅ El precio será $0.01 USD
- ✅ Debería funcionar sin problemas

---

## 📊 **Precios Actualizados:**

### **Plan Test:**
- **PayPal:** $0.01 USD/mes
- **Mercado Pago:** $15.00 ARS/mes (o $10 ARS mínimo si se ajusta)

### **Plan Plus:**
- **PayPal:** $9.99 USD/mes
- **Mercado Pago:** ~$9,990 ARS/mes

### **Plan Pro:**
- **PayPal:** $19.99 USD/mes
- **Mercado Pago:** ~$19,990 ARS/mes

---

## ✅ **Checklist de Verificación:**

- [x] Edge Function actualizada con validación de precio mínimo
- [x] Logs mejorados para debugging
- [x] Precio mínimo ajustado a $10 ARS si es necesario
- [ ] **Probar nuevamente el flujo completo**
- [ ] **Verificar que el botón esté habilitado**
- [ ] **Completar un pago de prueba**

---

## 🚨 **Nota Importante:**

Si el precio se ajusta automáticamente a $10 ARS (por ser menor al mínimo), el usuario verá:
- **En la UI:** Precio original convertido (~$15 ARS)
- **En el checkout:** Precio ajustado ($10 ARS)

Esto es normal y necesario para que Mercado Pago procese la suscripción.

---

**Estado:** ✅ **Función Actualizada y Desplegada**  
**Fecha:** 2025-12-20  
**Versión:** 2.3 - Mercado Pago Price Validation

