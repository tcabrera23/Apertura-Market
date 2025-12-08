# Revisión de Configuración SMTP - Brevo en Supabase

## ⚠️ Problema Detectado: Puerto SMTP

### Configuración Actual
- **Host:** `smtp-relay.brevo.com` ✅ Correcto
- **Port:** `585` ❌ **INCORRECTO**
- **Username:** `tomascabrera739@gmail.com` ✅ Correcto
- **Sender Email:** `noreply@aperturaia.com` ✅ Correcto
- **Sender Name:** `Bull Analytics` ✅ Correcto

### Problema con el Puerto 585

El puerto **585** no es un puerto estándar para SMTP. Brevo utiliza los siguientes puertos:

1. **Puerto 587 (STARTTLS)** - ✅ **RECOMENDADO**
   - Conexión segura con STARTTLS
   - Funciona con la mayoría de firewalls
   - Estándar de la industria

2. **Puerto 465 (SSL/TLS)** - ✅ Alternativa
   - Conexión SSL directa
   - También ampliamente soportado

3. **Puerto 25** - ❌ No recomendado
   - Generalmente bloqueado por ISPs
   - Mayor riesgo de ser marcado como spam

### Solución

**Cambiar el puerto de `585` a `587`** en la configuración de Supabase:

1. Ve a Supabase Dashboard → Settings → Auth → SMTP Settings
2. Cambia el **Port number** de `585` a `587`
3. Guarda los cambios

### Verificación Post-Cambio

Después de cambiar el puerto, verifica que los emails funcionen:

1. Envía un email de prueba desde tu aplicación
2. Revisa los logs de Supabase para errores SMTP
3. Verifica que el email llegue a la bandeja de entrada (no spam)

---

## ✅ Configuración Correcta Recomendada

```
Host: smtp-relay.brevo.com
Port: 587
Username: tomascabrera739@gmail.com
Password: [tu contraseña de Brevo]
Sender Email: noreply@aperturaia.com
Sender Name: Bull Analytics
Minimum interval per user: 60 seconds
```

---

## 📝 Notas Adicionales

### Autenticación del Dominio

Para mejorar la entregabilidad, asegúrate de que el dominio `aperturaia.com` tenga configurado:

1. **SPF Record:**
   ```
   v=spf1 include:spf.brevo.com ~all
   ```

2. **DKIM Record:**
   - Configúralo desde el panel de Brevo
   - Agrega el registro DNS que te proporcionen

3. **DMARC Record (Opcional pero recomendado):**
   ```
   v=DMARC1; p=quarantine; rua=mailto:dmarc@aperturaia.com
   ```

### Verificación en Brevo

1. Ve a tu cuenta de Brevo
2. Verifica que el dominio `aperturaia.com` esté verificado
3. Completa la configuración de SPF/DKIM si no lo has hecho

---

## 🔍 Troubleshooting

### Si los emails no se envían después del cambio:

1. **Verifica los logs de Supabase:**
   - Dashboard → Logs → Auth Logs
   - Busca errores relacionados con SMTP

2. **Verifica la contraseña:**
   - Asegúrate de que la contraseña en Supabase sea la correcta
   - En Brevo, genera una nueva contraseña SMTP si es necesario

3. **Verifica el firewall:**
   - Asegúrate de que el puerto 587 no esté bloqueado
   - Si usas un VPS, verifica las reglas de firewall

4. **Prueba la conexión SMTP:**
   ```bash
   # Desde tu servidor, prueba la conexión
   telnet smtp-relay.brevo.com 587
   # O con openssl
   openssl s_client -connect smtp-relay.brevo.com:587 -starttls smtp
   ```

---

## 📚 Referencias

- [Documentación de Brevo SMTP](https://help.brevo.com/hc/en-us/articles/209467485)
- [Configuración SMTP en Supabase](https://supabase.com/docs/guides/auth/auth-smtp)




