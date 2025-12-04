# 🚀 Guía de Migración a Producción: localhost → https://bullanalytics.io/

## 📋 Resumen Ejecutivo

Este documento describe el proceso completo para migrar BullAnalytics de un entorno de desarrollo local (`http://localhost:8080`) a producción (`https://bullanalytics.io/`).

**Fecha de Migración:** [FECHA A COMPLETAR]  
**Dominio de Producción:** `https://bullanalytics.io/`  
**Dominio de Desarrollo:** `http://localhost:8080` (mantener para desarrollo local)

---

## 🎯 Objetivos de la Migración

1. ✅ Configurar todas las URLs para usar `https://bullanalytics.io/`
2. ✅ Actualizar configuraciones de servicios externos (Supabase, PayPal, n8n)
3. ✅ Mantener compatibilidad con desarrollo local mediante variables de entorno
4. ✅ Actualizar templates de email con URLs de producción
5. ✅ Configurar CORS correctamente para el nuevo dominio

---

## 📦 Servicios Externos a Configurar

### 1. Supabase

#### 1.1. Configuración de Redirect URLs

**Dashboard de Supabase:** https://supabase.com/dashboard/project/pwumamzbicapuiqkwrey

**URLs a actualizar:**

1. **Authentication → URL Configuration:**
   - **Site URL:** `https://bullanalytics.io/`
   - **Redirect URLs:** Agregar:
     ```
     https://bullanalytics.io/login.html
     https://bullanalytics.io/dashboard.html
     https://bullanalytics.io/reset-password.html
     https://bullanalytics.io/subscription-success.html
     ```

2. **OAuth Providers (Google, Microsoft):**
   - **Redirect URLs en Google Cloud Console:**
     - Mantener: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback`
     - Agregar (si es necesario): `https://bullanalytics.io/login.html`
   
   - **Redirect URLs en Azure AD (Microsoft):**
     - Mantener: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback`
     - Agregar (si es necesario): `https://bullanalytics.io/login.html`

#### 1.2. Webhooks de Supabase

Si tienes webhooks configurados en Supabase que apuntan a tu backend:
- Actualizar URL del webhook a: `https://bullanalytics.io/api/webhooks/supabase` (o la ruta correspondiente)

---

### 2. PayPal

#### 2.1. PayPal Developer Dashboard

**URL:** https://developer.paypal.com/dashboard/

**Configuraciones a actualizar:**

1. **Return URL:**
   - **Desarrollo (Sandbox):** `http://localhost:8080/subscription-success.html`
   - **Producción (Live):** `https://bullanalytics.io/subscription-success.html`

2. **Cancel URL:**
   - **Desarrollo (Sandbox):** `http://localhost:8080/pricing.html`
   - **Producción (Live):** `https://bullanalytics.io/pricing.html`

3. **Webhook URL:**
   - **Producción:** `https://bullanalytics.io/api/webhooks/paypal`
   - Verificar que el webhook esté activo y configurado correctamente

#### 2.2. Pasos en PayPal Dashboard

1. Ir a **My Apps & Credentials** → Seleccionar tu app de producción
2. En **App Settings**, verificar:
   - Return URL: `https://bullanalytics.io/subscription-success.html`
   - Cancel URL: `https://bullanalytics.io/pricing.html`
3. En **Webhooks**, verificar:
   - Webhook URL: `https://bullanalytics.io/api/webhooks/paypal`
   - Eventos suscritos: `BILLING.SUBSCRIPTION.*`, `PAYMENT.*`

---

### 3. n8n (Automatizaciones)

Si utilizas n8n para automatizaciones:

#### 3.1. Webhooks de n8n

**URLs a actualizar:**

1. **Webhooks que reciben datos de BullAnalytics:**
   - Actualizar URL base de: `http://localhost:8080` → `https://bullanalytics.io`

2. **Webhooks que envían datos a BullAnalytics:**
   - Verificar que las URLs de callback apunten a: `https://bullanalytics.io/api/webhooks/n8n` (o la ruta correspondiente)

#### 3.2. Configuración en n8n

1. Ir a tu instancia de n8n
2. Buscar todos los workflows que interactúan con BullAnalytics
3. Actualizar:
   - **HTTP Request nodes:** Cambiar URLs de `localhost:8080` a `bullanalytics.io`
   - **Webhook nodes:** Verificar que las URLs de callback sean correctas
   - **Variables de entorno:** Actualizar `API_BASE_URL` si está configurada

---

### 4. Brevo (Email Service)

No requiere cambios específicos, pero verificar:
- **Sender Email:** Debe estar verificado para el dominio `bullanalytics.io`
- **SPF/DKIM Records:** Configurar en DNS si es necesario

---

## 🔧 Variables de Entorno

### Archivo `.env` de Producción

Crear un archivo `.env.production` con las siguientes variables:

```bash
# ============================================
# DOMAIN CONFIGURATION
# ============================================
FRONTEND_URL=https://bullanalytics.io
API_BASE_URL=https://bullanalytics.io/api
AUTH_API_BASE_URL=https://bullanalytics.io/auth

# ============================================
# SUPABASE CONFIGURATION
# ============================================
SUPABASE_URL=https://pwumamzbicapuiqkwrey.supabase.co
SUPABASE_SERVICE_KEY=YOUR_SERVICE_KEY
SUPABASE_ANON_KEY=YOUR_ANON_KEY
SUPABASE_JWT_SECRET=YOUR_JWT_SECRET

# ============================================
# PAYPAL CONFIGURATION
# ============================================
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=YOUR_LIVE_CLIENT_ID
PAYPAL_CLIENT_SECRET=YOUR_LIVE_CLIENT_SECRET
PAYPAL_RETURN_URL=https://bullanalytics.io/subscription-success.html
PAYPAL_CANCEL_URL=https://bullanalytics.io/pricing.html

# ============================================
# EMAIL CONFIGURATION (Brevo)
# ============================================
BREVO_API_KEY=YOUR_BREVO_API_KEY

# ============================================
# OTHER SERVICES
# ============================================
GROQ_API_KEY=YOUR_GROQ_API_KEY
```

---

## 📝 Archivos a Modificar

### Backend (Python)

#### 1. `app_supabase.py`

**Ubicaciones a modificar:**

```python
# Línea ~72-73: PayPal URLs
# ANTES (comentar):
# PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "http://localhost:8080/subscription-success.html")
# PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "http://localhost:8080/pricing.html")

# DESPUÉS (agregar):
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "https://bullanalytics.io/subscription-success.html")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "https://bullanalytics.io/pricing.html")

# Línea ~2022: Email redirect
# ANTES (comentar):
# "email_redirect_to": f"{os.getenv('FRONTEND_URL', 'http://localhost:8080')}/login.html"

# DESPUÉS (agregar):
"email_redirect_to": f"{os.getenv('FRONTEND_URL', 'https://bullanalytics.io')}/login.html"

# Línea ~2246: Reset password redirect
# ANTES (comentar):
# "redirect_to": f"{os.getenv('FRONTEND_URL', 'http://localhost:8080')}/reset-password.html"

# DESPUÉS (agregar):
"redirect_to": f"{os.getenv('FRONTEND_URL', 'https://bullanalytics.io')}/reset-password.html"

# Línea ~3059: Email template link
# ANTES (comentar):
# <a href="http://localhost:8080/rules.html" class="button">Gestionar Alertas</a>

# DESPUÉS (agregar):
<a href="https://bullanalytics.io/rules.html" class="button">Gestionar Alertas</a>

# Línea ~3710: Server print
# ANTES (comentar):
# print("📡 Server: http://localhost:8080")

# DESPUÉS (agregar):
print("📡 Server: https://bullanalytics.io")
```

#### 2. `main_login.py` (si existe)

**Ubicaciones a modificar:**

```python
# Línea ~521: OAuth redirect
# ANTES (comentar):
# redirect_to = "http://localhost:8080/login.html"

# DESPUÉS (agregar):
redirect_to = os.getenv("FRONTEND_URL", "https://bullanalytics.io") + "/login.html"

# Línea ~561: Callback redirect
# ANTES (comentar):
# frontend_url = "http://localhost:8080/login.html"

# DESPUÉS (agregar):
frontend_url = os.getenv("FRONTEND_URL", "https://bullanalytics.io") + "/login.html"

# Línea ~50: CORS origins
# ANTES (comentar):
# cors_origins: str = "http://localhost:8080,http://localhost:8000,http://127.0.0.1:8000"

# DESPUÉS (agregar):
cors_origins: str = "https://bullanalytics.io,http://localhost:8080,http://localhost:8000"
```

#### 3. `email_templates.py`

**Ubicaciones a modificar:**

```python
# Línea ~135: Dashboard link
# ANTES (comentar):
# <a href="http://localhost:8080/dashboard.html" class="button">Ir al Dashboard</a>

# DESPUÉS (agregar):
<a href="https://bullanalytics.io/dashboard.html" class="button">Ir al Dashboard</a>

# Línea ~321-322: Alert email links
# ANTES (comentar):
# <a href="http://localhost:8080/dashboard.html" class="button">Ver Dashboard</a>
# <a href="http://localhost:8080/rules.html" class="button" style="background: #6c757d; margin-left: 10px;">Gestionar Alertas</a>

# DESPUÉS (agregar):
<a href="https://bullanalytics.io/dashboard.html" class="button">Ver Dashboard</a>
<a href="https://bullanalytics.io/rules.html" class="button" style="background: #6c757d; margin-left: 10px;">Gestionar Alertas</a>
```

### Frontend (JavaScript)

#### 1. `js/account.js`

```javascript
// Línea ~6: API Base URL
// ANTES (comentar):
// window.API_BASE_URL = 'http://localhost:8080/api';

// DESPUÉS (agregar):
window.API_BASE_URL = window.location.origin + '/api';
// O para producción específicamente:
// window.API_BASE_URL = 'https://bullanalytics.io/api';

// Línea ~11: Auth API Base URL
// ANTES (comentar):
// window.AUTH_API_BASE_URL = 'http://localhost:8080/auth';

// DESPUÉS (agregar):
window.AUTH_API_BASE_URL = window.location.origin + '/auth';
// O para producción específicamente:
// window.AUTH_API_BASE_URL = 'https://bullanalytics.io/auth';

// Línea ~33: User endpoint
// ANTES (comentar):
// const userResponse = await fetch(`http://localhost:8080/api/v1/user/me`, {

// DESPUÉS (agregar):
const userResponse = await fetch(`${window.API_BASE_URL}/v1/user/me`, {
```

#### 2. `account.html`

```html
<!-- Línea ~266: API Base URL (comentado) -->
<!-- const API_BASE_URL = 'http://localhost:8080/api'; NO DEBERIA ESTAR DEFINIDO -->

<!-- Línea ~816: API Base URL inline -->
<!-- ANTES (comentar): -->
<!-- const API_BASE_URL = 'http://localhost:8080/api'; -->

<!-- DESPUÉS (agregar): -->
const API_BASE_URL = window.location.origin + '/api';
// O para producción específicamente:
// const API_BASE_URL = 'https://bullanalytics.io/api';
```

#### 3. `js/login.js`

```javascript
// Línea ~4: Auth API Base URL
// ANTES (comentar):
// const AUTH_API_BASE_URL = 'http://localhost:8080/auth';

// DESPUÉS (agregar):
const AUTH_API_BASE_URL = window.location.origin + '/auth';
// O para producción específicamente:
// const AUTH_API_BASE_URL = 'https://bullanalytics.io/auth';
```

#### 4. `js/dashboard.js`

```javascript
// Línea ~4: API Base URL
// ANTES (comentar):
// const API_BASE_URL = 'http://localhost:8080/api';

// DESPUÉS (agregar):
const API_BASE_URL = window.location.origin + '/api';
// O para producción específicamente:
// const API_BASE_URL = 'https://bullanalytics.io/api';
```

#### 5. `js/charts.js`

```javascript
// Línea ~739: API Base URL
// ANTES (comentar):
// const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080/api';

// DESPUÉS (agregar):
const API_BASE_URL = window.API_BASE_URL || window.location.origin + '/api';
// O para producción específicamente:
// const API_BASE_URL = window.API_BASE_URL || 'https://bullanalytics.io/api';
```

#### 6. `js/rules.js`

```javascript
// Línea ~4: API Base URL
// ANTES (comentar):
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080/api';

// DESPUÉS (agregar):
const getApiBaseUrl = () => window.API_BASE_URL || window.location.origin + '/api';
```

#### 7. `js/calendar.js`

```javascript
// Línea ~3: API Base URL
// ANTES (comentar):
// const API_BASE_URL = 'http://localhost:8080/api';

// DESPUÉS (agregar):
const API_BASE_URL = window.location.origin + '/api';
```

#### 8. `js/news.js`

```javascript
// Línea ~4: API Base URL
// ANTES (comentar):
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080/api';

// DESPUÉS (agregar):
const getApiBaseUrl = () => window.API_BASE_URL || window.location.origin + '/api';
```

#### 9. `js/table-config.js`

```javascript
// Línea ~5: API Base URL
// ANTES (comentar):
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080/api';

// DESPUÉS (agregar):
const getApiBaseUrl = () => window.API_BASE_URL || window.location.origin + '/api';
```

#### 10. `js/google-translate.js`

```javascript
// Línea ~95: API Base URL
// ANTES (comentar):
// const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080';

// DESPUÉS (agregar):
const API_BASE_URL = window.API_BASE_URL || window.location.origin;
```

#### 11. `js/reset-password.js`

```javascript
// Línea ~2: API Base URL
// ANTES (comentar):
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080';

// DESPUÉS (agregar):
const getApiBaseUrl = () => window.API_BASE_URL || window.location.origin;
```

#### 12. `js/forgot-password.js`

```javascript
// Línea ~2: API Base URL
// ANTES (comentar):
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080';

// DESPUÉS (agregar):
const getApiBaseUrl = () => window.API_BASE_URL || window.location.origin;
```

---

## 🔄 Estrategia de Migración Recomendada

### Fase 1: Preparación (Pre-Migración)

1. ✅ **Backup completo del código actual**
2. ✅ **Documentar todas las configuraciones actuales**
3. ✅ **Crear rama de git:** `git checkout -b migration/production-domain`
4. ✅ **Configurar variables de entorno de producción**

### Fase 2: Actualización de Código

1. ✅ **Actualizar archivos backend** (`app_supabase.py`, `main_login.py`, `email_templates.py`)
2. ✅ **Actualizar archivos frontend** (todos los `.js` y `.html`)
3. ✅ **Comentar líneas de localhost** (no eliminar, solo comentar)
4. ✅ **Agregar líneas con dominio de producción**
5. ✅ **Usar `window.location.origin` cuando sea posible** para hacer el código más flexible

### Fase 3: Configuración de Servicios Externos

1. ✅ **Supabase:**
   - Actualizar Site URL
   - Actualizar Redirect URLs
   - Verificar OAuth providers

2. ✅ **PayPal:**
   - Actualizar Return/Cancel URLs en producción
   - Verificar webhook URL
   - Probar flujo completo

3. ✅ **n8n:**
   - Actualizar webhooks
   - Actualizar HTTP Request nodes
   - Verificar variables de entorno

### Fase 4: Testing

1. ✅ **Testing local con variables de entorno de producción**
2. ✅ **Testing en staging (si existe)**
3. ✅ **Testing en producción (después del deploy)**

### Fase 5: Deploy

1. ✅ **Deploy a producción**
2. ✅ **Verificar que todos los servicios funcionen**
3. ✅ **Monitorear logs y errores**
4. ✅ **Verificar emails de onboarding**

---

## 🧪 Checklist de Verificación Post-Migración

### Funcionalidades Core

- [ ] Registro de usuarios funciona
- [ ] Login funciona
- [ ] OAuth (Google/Microsoft) funciona
- [ ] Reset password funciona
- [ ] Dashboard carga correctamente
- [ ] Gráficos se renderizan
- [ ] Watchlists funcionan
- [ ] Alertas funcionan

### Integraciones

- [ ] Emails de onboarding se envían correctamente
- [ ] Links en emails apuntan a `bullanalytics.io`
- [ ] PayPal checkout funciona
- [ ] PayPal webhooks reciben eventos
- [ ] Supabase redirects funcionan
- [ ] n8n webhooks funcionan (si aplica)

### URLs y Redirects

- [ ] Todas las URLs usan `https://bullanalytics.io`
- [ ] No hay referencias a `localhost` en producción
- [ ] CORS está configurado correctamente
- [ ] OAuth redirects funcionan

---

## 🐛 Troubleshooting

### Problema: OAuth no funciona después de la migración

**Solución:**
1. Verificar que las Redirect URLs en Supabase incluyan `https://bullanalytics.io/login.html`
2. Verificar que Google Cloud Console tenga el callback de Supabase configurado
3. Verificar CORS en el backend

### Problema: PayPal no redirige correctamente

**Solución:**
1. Verificar `PAYPAL_RETURN_URL` y `PAYPAL_CANCEL_URL` en variables de entorno
2. Verificar configuración en PayPal Dashboard
3. Verificar que el webhook esté activo

### Problema: Emails tienen links a localhost

**Solución:**
1. Verificar que `email_templates.py` esté actualizado
2. Verificar que `FRONTEND_URL` esté configurado en variables de entorno
3. Reiniciar el servidor después de cambios

### Problema: API calls fallan con CORS

**Solución:**
1. Verificar que `CORS_ORIGINS` incluya `https://bullanalytics.io`
2. Verificar que el backend esté configurado para aceptar requests del nuevo dominio
3. Verificar headers en las requests

---

## 📚 Referencias

- **Supabase Dashboard:** https://supabase.com/dashboard/project/pwumamzbicapuiqkwrey
- **PayPal Developer Dashboard:** https://developer.paypal.com/dashboard/
- **Documentación de Supabase Auth:** https://supabase.com/docs/guides/auth
- **Documentación de PayPal Subscriptions:** https://developer.paypal.com/docs/subscriptions/

---

## 📝 Notas Adicionales

1. **Mantener compatibilidad con desarrollo local:**
   - Usar variables de entorno para URLs
   - Usar `window.location.origin` en frontend cuando sea posible
   - Comentar (no eliminar) código de localhost

2. **SSL/HTTPS:**
   - Asegurarse de que el certificado SSL esté configurado correctamente
   - Verificar que todas las URLs usen `https://`

3. **Performance:**
   - Después de la migración, monitorear tiempos de respuesta
   - Verificar que CDN (si existe) esté configurado correctamente

4. **Monitoreo:**
   - Configurar alertas para errores 500
   - Monitorear logs de Supabase, PayPal, y n8n
   - Verificar que los webhooks estén recibiendo eventos

---

**Última actualización:** [FECHA]  
**Versión del documento:** 1.0  
**Autor:** Equipo de Desarrollo BullAnalytics

