# 🔐 Guía de Configuración OAuth - BullAnalytics

## 📋 Configuración Actual

### Callback URLs Configurados

**Para Google OAuth en Supabase:**
- Callback URL: `http://localhost:8080/login.html`
- Este es el URL que debe estar configurado en Google Cloud Console

**Flujo OAuth:**
1. Usuario hace clic en "Continuar con Google" en `login.html`
2. Redirige a Supabase OAuth: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/authorize?provider=google&redirect_to=http://localhost:8080/login.html`
3. Google autentica al usuario
4. Google redirige a Supabase con el código
5. Supabase procesa y redirige a `http://localhost:8080/login.html#access_token=...`
6. `login.js` captura el token del hash fragment
7. `login.js` llama a `/auth/oauth/complete` para persistir el usuario
8. Usuario es redirigido a `dashboard.html`

## 🔧 Configuración en Google Cloud Console

### Paso 1: Configurar OAuth en Supabase Dashboard

1. Ve a tu proyecto en Supabase: https://supabase.com/dashboard/project/pwumamzbicapuiqkwrey
2. Ve a **Authentication** → **Providers** → **Google**
3. Habilita "Enable Sign in with Google"
4. Configura:
   - **Client IDs**: Tu Client ID de Google Cloud Console
   - **Client Secret**: Tu Client Secret de Google Cloud Console
   - **Callback URL**: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback`
     - ⚠️ Este es el callback de Supabase, NO el de tu app local

### Paso 2: Configurar en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a **APIs & Services** → **Credentials**
4. Edita tu OAuth 2.0 Client ID
5. En **Authorized redirect URIs**, agrega:
   ```
   https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback
   ```
   - ⚠️ Este es el callback de Supabase, NO `localhost:8080`

### Paso 3: Verificar Configuración

**En Supabase Dashboard:**
- ✅ Callback URL mostrado: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback`
- ✅ Este URL debe estar en Google Cloud Console como "Authorized redirect URI"

**En tu aplicación:**
- ✅ `main_login.py` redirige a: `http://localhost:8080/login.html`
- ✅ `login.html` captura el token del hash fragment
- ✅ `login.js` completa el flujo llamando a `/auth/oauth/complete`

## 🚀 Cómo Funciona

### Arquitectura

```
Usuario → login.html (puerto 8080)
    ↓
Clic en "Continuar con Google"
    ↓
main_login.py (puerto 8000) → /auth/oauth/google
    ↓
Redirige a Supabase OAuth
    ↓
Supabase → Google OAuth
    ↓
Google autentica → Supabase
    ↓
Supabase → http://localhost:8080/login.html#access_token=...
    ↓
login.js captura token
    ↓
login.js → main_login.py /auth/oauth/complete
    ↓
Usuario persistido → Redirige a dashboard.html
```

## ⚠️ Puntos Importantes

1. **Callback URL en Google Cloud Console:**
   - Debe ser: `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback`
   - NO debe ser `localhost:8080` (eso es solo para desarrollo local)

2. **Redirect URL en main_login.py:**
   - Está configurado para: `http://localhost:8080/login.html`
   - Este es el URL al que Supabase redirige después de autenticar

3. **CORS:**
   - `main_login.py` tiene configurado CORS para aceptar requests de `localhost:8080`

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"
- **Causa**: El callback URL en Google Cloud Console no coincide
- **Solución**: Asegúrate de que `https://pwumamzbicapuiqkwrey.supabase.co/auth/v1/callback` esté en "Authorized redirect URIs"

### Error: "Token no encontrado"
- **Causa**: El hash fragment no se está capturando correctamente
- **Solución**: Verifica que `login.js` esté ejecutando `handleOAuthCallback()` al cargar

### Error: CORS
- **Causa**: `main_login.py` no tiene configurado CORS para `localhost:8080`
- **Solución**: Ya está configurado en `cors_origins`

## 📝 Notas

- El callback URL en Supabase Dashboard es solo informativo
- El callback real que Google usa es el configurado en Google Cloud Console
- Para producción, necesitarás configurar el callback URL de producción en ambos lugares

---

**Última actualización**: Diciembre 2025

