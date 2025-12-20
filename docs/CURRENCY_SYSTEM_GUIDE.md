# 💰 Sistema de Monedas Multi-País - Guía Completa

## 📋 Resumen

Este sistema detecta automáticamente el país del usuario y muestra los precios en su moneda local, mientras mantiene la integridad de los pagos en las monedas correctas:

- **Mercado Pago:** Siempre cobra en **ARS** (Pesos Argentinos)
- **PayPal:** Siempre cobra en **USD** (Dólares)

## 🌍 Países y Monedas Soportados

| País | Código | Moneda | Símbolo | Plataforma Recomendada |
|------|--------|--------|---------|------------------------|
| Argentina | AR | ARS | $ | Mercado Pago |
| Uruguay | UY | UYU | $ | Mercado Pago |
| Chile | CL | CLP | $ | Mercado Pago |
| Brasil | BR | BRL | R$ | Mercado Pago |
| México | MX | MXN | $ | Mercado Pago |
| Colombia | CO | COP | $ | Mercado Pago |
| Perú | PE | PEN | S/ | Mercado Pago |
| **Resto del mundo** | DEFAULT | USD | $ | PayPal |

## 🔧 Componentes del Sistema

### 1. **Frontend - `js/currency-handler.js`**

**Funciones principales:**
- `detectUserCountry()`: Detecta el país del usuario usando IP geolocalización
- `getExchangeRates()`: Obtiene tasas de cambio desde API externa (con cache de 1 hora)
- `convertPrice(priceUSD, targetCurrency)`: Convierte USD a la moneda destino
- `formatPrice(price, currencyCode)`: Formatea el precio con el símbolo correcto
- `updateAllPrices()`: Actualiza todos los precios en la página automáticamente

**Atributos HTML para precios:**
```html
<!-- Precio simple (ej: "Gratis" o "$9.99") -->
<div data-price-plan="plus">$9.99</div>

<!-- Precio con período (ej: "$9.99/mes") -->
<div data-price-with-period="plus" data-period="mes">$9.99<span>/mes</span></div>
```

**Cache:**
- Tasas de cambio: 1 hora en memoria
- Info de moneda del usuario: `localStorage` como `user_currency`

### 2. **Backend - Edge Function `vexor-payments/index.ts`**

**Lógica de conversión:**
```typescript
if (platform === 'mercadopago') {
  currency = 'ARS'
  const exchangeRate = await getExchangeRate() // Llama a API de tasas
  finalPrice = Math.round(parseFloat(plan.price) * exchangeRate)
}
```

**API de tasas de cambio:**
- URL: `https://api.exchangerate-api.com/v4/latest/USD`
- Fallback: 1000 (aproximado) si la API falla
- Redondeo: Sin decimales para ARS, CLP, COP

**Metadata enviada a Vexor:**
```json
{
  "user_id": "uuid",
  "plan_id": "uuid",
  "coupon_code": "optional",
  "original_price_usd": "9.99",
  "currency": "ARS"
}
```

### 3. **Frontend - Modal de Selección de Plataforma**

El modal en `js/subscription.js` ahora muestra:
- La plataforma **recomendada** según el país (con badge amarillo)
- La moneda que se usará para cada plataforma:
  - **PayPal:** siempre USD
  - **Mercado Pago:** siempre ARS

```javascript
// Ejemplo de uso
showPlatformSelector('plus', buttonElement)
```

## 🎨 Experiencia de Usuario

### Flujo para usuario Argentino:

1. **Página de Pricing:**
   - Ve: "Plan Plus - $9990/mes" (convertido a ARS)
   - Badge: "💰 Precios en ARS" (aparece 5 segundos)

2. **Clic en "Comenzar Ahora":**
   - Modal se abre con **Mercado Pago recomendado** (badge amarillo)
   - Texto: "Pagar con Mercado Pago (ARS)"

3. **Selecciona Mercado Pago:**
   - Edge Function convierte $9.99 USD → $9990 ARS (al tipo de cambio actual)
   - Vexor crea suscripción en Mercado Pago por $9990 ARS/mes
   - Usuario redirigido al checkout de Mercado Pago

4. **Pago completado:**
   - Webhook actualiza `subscriptions` con `platform: "mercadopago"` y `currency: "ARS"`

### Flujo para usuario de USA:

1. **Página de Pricing:**
   - Ve: "Plan Plus - $9.99/month"
   - No hay badge de moneda (ya está en USD)

2. **Clic en "Comenzar Ahora":**
   - Modal se abre con **PayPal recomendado** (badge amarillo)
   - Texto: "Pagar con PayPal (USD)"

3. **Selecciona PayPal:**
   - Edge Function mantiene precio en $9.99 USD
   - Vexor crea suscripción en PayPal por $9.99 USD/mes
   - Usuario redirigido al checkout de PayPal

## 📊 Precios Base (USD)

Definidos en `js/currency-handler.js` y deben coincidir con la base de datos:

```javascript
const BASE_PRICES_USD = {
    'free': 0,
    'plus': 9.99,
    'pro': 19.99
}
```

## 🔄 Actualización de Tasas de Cambio

**API usada:** [exchangerate-api.com](https://api.exchangerate-api.com/v4/latest/USD)
- Gratuita, sin API key requerida
- Límite: ilimitado para uso básico
- Actualizaciones: diarias

**Estructura de respuesta:**
```json
{
  "rates": {
    "ARS": 1000.5,
    "BRL": 5.7,
    "CLP": 950,
    ...
  }
}
```

**Valores fallback (si falla la API):**
```javascript
{
  ARS: 1000,
  UYU: 43,
  CLP: 950,
  BRL: 5.7,
  MXN: 18,
  COP: 4300,
  PEN: 3.7,
  USD: 1
}
```

## 🚀 Deploy de Edge Function

```bash
# 1. Linkear proyecto (si no lo hiciste)
npx supabase link --project-ref pwumamzbicapuiqkwrey

# 2. Deployar la Edge Function actualizada
npx supabase functions deploy vexor-payments --no-verify-jwt --project-ref pwumamzbicapuiqkwrey
```

## 🧪 Testing

### Probar detección de país:

1. Abrir DevTools → Console
2. Ejecutar: `window.CurrencyHandler.detectUserCountry()`
3. Verificar país detectado

### Probar conversión de precios:

```javascript
// Convertir $9.99 USD a ARS
window.CurrencyHandler.convertPrice(9.99, 'ARS').then(console.log)
// Output esperado: ~9990

// Ver tasas actuales
window.CurrencyHandler.getExchangeRates().then(console.log)
```

### Simular usuario de Argentina:

1. Usar VPN o proxy en Argentina
2. O forzar en localStorage:
```javascript
localStorage.setItem('user_currency', JSON.stringify({
  code: 'ARS',
  symbol: '$',
  name: 'Peso Argentino',
  platform: 'mercadopago'
}))
```
3. Recargar página

## 🔐 Seguridad

- ✅ Las conversiones en el frontend son **solo visuales**
- ✅ El precio real se calcula en la **Edge Function (backend)**
- ✅ Vexor recibe el precio ya convertido correctamente
- ✅ No es posible manipular precios desde el navegador

## 📝 Notas Importantes

1. **Los precios en la página se actualizan automáticamente** al cargar.
2. **El indicador de moneda aparece solo si NO es USD**.
3. **Mercado Pago siempre cobra en ARS**, incluso si el usuario selecciona otra moneda latinoamericana (Vexor maneja la conversión interna si es necesario).
4. **PayPal siempre cobra en USD**, sin excepciones.
5. **Las tasas de cambio se cachean 1 hora** para evitar exceso de llamadas a la API.

## 🐛 Troubleshooting

### Los precios no se actualizan:
- Verificar que `js/currency-handler.js` se cargue antes que `js/subscription.js`
- Verificar en Console que no hay errores de la API de tasas

### API de geolocalización falla:
- El sistema usa fallback basado en idioma del navegador
- Por defecto asume 'US' si no puede detectar

### Precios incorrectos en Vexor:
- Verificar que la Edge Function esté usando las tasas de cambio actualizadas
- Ver logs en Supabase Dashboard → Edge Functions → vexor-payments

## 🔗 URLs de Testing

- **Sandbox API (tasas):** https://api.exchangerate-api.com/v4/latest/USD
- **IP Geolocation (gratuita):** https://ipapi.co/json/
- **Vexor Dashboard:** https://vexorpay.com/dashboard

## ✅ Checklist de Deploy

- [x] Edge Function actualizada con conversión de monedas
- [x] Frontend con `currency-handler.js`
- [x] `index.html` con atributos data-price
- [x] `pricing.html` con atributos data-price
- [x] Modal de selección con plataforma recomendada
- [x] Webhook en FastAPI actualizado para recibir `currency` y `platform`
- [ ] **Deployar Edge Function a Supabase**
- [ ] **Probar flujo completo con tarjetas de test**

---

**Última actualización:** 2025-12-20
**Versión:** 2.0 - Sistema Multi-Moneda con Vexor

