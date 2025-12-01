# Guía de Envío de Alertas por Correo Electrónico

## ❌ ¿Por qué NO usar tu correo personal?

**NO es recomendable** usar tu correo personal (Gmail, Outlook, Yahoo, etc.) directamente porque:

1. **Límites estrictos de envío:**
   - Gmail: máximo 500 correos/día (cuenta personal)
   - Outlook: máximo 300 correos/día
   - Riesgo de bloqueo permanente si excedes los límites

2. **Problemas de entregabilidad:**
   - Los correos pueden ir a spam
   - No hay garantía de entrega
   - Sin analytics de entrega/rebotes

3. **Riesgo de seguridad:**
   - Exponer tu contraseña personal
   - Si tu app es comprometida, tu cuenta personal está en riesgo

4. **No es escalable:**
   - Con 10 usuarios activos, fácilmente superarás los límites
   - No puedes enviar correos masivos

---

## ✅ Opciones Recomendadas

### 1. **Brevo (Sendinblue)** - ⭐ RECOMENDADO para empezar

**Ventajas:**
- ✅ **Plan GRATUITO**: 300 correos/día (9,000/mes)
- ✅ API REST fácil de usar
- ✅ Dashboard con analytics
- ✅ Buena entregabilidad
- ✅ Soporte para templates HTML
- ✅ No requiere configuración SMTP compleja

**Límites del plan gratuito:**
- 300 correos/día
- 9,000 correos/mes
- Sin límite de contactos
- Analytics básicos

**Precios:**
- Gratis: 300/día
- Lite ($25/mes): 10,000/mes
- Premium ($65/mes): 20,000/mes

**Ideal para:** Proyectos pequeños/medianos, desarrollo, MVP

---

### 2. **Resend** - Moderno y simple

**Ventajas:**
- ✅ API muy simple (similar a SendGrid)
- ✅ Plan gratuito: 3,000 correos/mes
- ✅ Excelente para correos transaccionales
- ✅ Buena documentación

**Límites del plan gratuito:**
- 3,000 correos/mes
- 100 correos/día

**Ideal para:** Aplicaciones modernas, correos transaccionales

---

### 3. **SendGrid** - Empresarial

**Ventajas:**
- ✅ Plan gratuito: 100 correos/día
- ✅ Muy confiable y escalable
- ✅ Excelente para alto volumen
- ✅ Analytics avanzados

**Límites del plan gratuito:**
- 100 correos/día (3,000/mes)

**Ideal para:** Aplicaciones empresariales, alto volumen

---

### 4. **Amazon SES** - Más económico a escala

**Ventajas:**
- ✅ Muy económico: $0.10 por 1,000 correos
- ✅ Escalable
- ✅ Integración con AWS

**Desventajas:**
- ❌ Configuración más compleja
- ❌ Requiere verificación de dominio
- ❌ No es ideal para empezar

**Ideal para:** Alto volumen, aplicaciones en AWS

---

## 🚀 Implementación Recomendada: Brevo

### Paso 1: Crear cuenta en Brevo

1. Ve a [brevo.com](https://www.brevo.com)
2. Crea una cuenta gratuita
3. Verifica tu email

### Paso 2: Obtener API Key

1. Ve a **Settings** → **API Keys**
2. Crea una nueva API Key
3. Copia la clave (solo se muestra una vez)

### Paso 3: Instalar librería Python

```bash
pip install sib-api-v3-sdk
```

### Paso 4: Implementar en `app_supabase.py`

```python
import os
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException

# Configurar Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

def send_alert_email(to_email: str, subject: str, html_content: str):
    """Envía un correo de alerta usando Brevo"""
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY no configurada")
        return False
    
    try:
        configuration = Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        
        api_instance = TransactionalEmailsApi(ApiClient(configuration))
        
        send_smtp_email = {
            'sender': {
                'name': 'BullAnalytics',
                'email': 'noreply@bullanalytics.com'  # Cambiar por tu dominio
            },
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': html_content
        }
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email enviado a {to_email}: {api_response.message_id}")
        return True
        
    except ApiException as e:
        logger.error(f"Error enviando email: {e}")
        return False
```

### Paso 5: Crear función para verificar reglas y enviar alertas

```python
async def check_and_send_alerts():
    """Verifica las reglas activas y envía alertas si se cumplen"""
    try:
        # Obtener todas las reglas activas
        response = supabase.table("rules") \
            .select("*") \
            .eq("is_active", True) \
            .execute()
        
        rules = response.data if response.data else []
        
        for rule in rules:
            # Obtener datos del activo
            asset_data = get_asset_data(rule['ticker'], rule['ticker'])
            
            if not asset_data:
                continue
            
            should_alert = False
            alert_message = ""
            
            # Verificar condición según el tipo de regla
            if rule['rule_type'] == 'price_below':
                if asset_data['current_price'] < rule['value_threshold']:
                    should_alert = True
                    alert_message = f"{rule['ticker']} está por debajo de ${rule['value_threshold']}"
            
            elif rule['rule_type'] == 'price_above':
                if asset_data['current_price'] > rule['value_threshold']:
                    should_alert = True
                    alert_message = f"{rule['ticker']} está por encima de ${rule['value_threshold']}"
            
            # ... otros tipos de reglas
            
            if should_alert:
                # Verificar si ya se envió una alerta recientemente (evitar spam)
                last_triggered = rule.get('last_triggered')
                if last_triggered:
                    last_triggered_dt = datetime.fromisoformat(last_triggered.replace('Z', '+00:00'))
                    if (datetime.now() - last_triggered_dt).total_seconds() < 3600:  # 1 hora
                        continue
                
                # Crear alerta en la base de datos
                alert_data = {
                    'user_id': rule['user_id'],
                    'rule_id': rule['id'],
                    'ticker': rule['ticker'],
                    'alert_type': rule['rule_type'],
                    'message': alert_message,
                    'is_read': False
                }
                supabase.table("alerts").insert(alert_data).execute()
                
                # Enviar correo
                html_content = f"""
                <html>
                    <body>
                        <h2>🚨 Alerta de BullAnalytics</h2>
                        <p><strong>{alert_message}</strong></p>
                        <p>Precio actual: ${asset_data['current_price']}</p>
                        <p>Regla: {rule['name']}</p>
                        <hr>
                        <p><small>Puedes gestionar tus alertas en tu panel de control.</small></p>
                    </body>
                </html>
                """
                
                send_alert_email(
                    to_email=rule['email'],
                    subject=f"Alerta: {rule['ticker']} - {alert_message}",
                    html_content=html_content
                )
                
                # Actualizar last_triggered
                supabase.table("rules") \
                    .update({'last_triggered': datetime.now().isoformat()}) \
                    .eq('id', rule['id']) \
                    .execute()
                
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}", exc_info=True)
```

### Paso 6: Configurar tarea programada (Cron Job)

Puedes usar:
- **Supabase Edge Functions** con cron triggers
- **Python APScheduler** en tu servidor
- **Cron job** en Linux
- **Cloud Functions** (Google Cloud, AWS Lambda)

Ejemplo con APScheduler:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_alerts, 'interval', minutes=15)
scheduler.start()
```

---

## 📊 Comparación Rápida

| Servicio | Plan Gratuito | Fácil de usar | Escalable | Recomendado para |
|----------|---------------|---------------|-----------|------------------|
| **Brevo** | 300/día | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Empezar, MVP |
| **Resend** | 3,000/mes | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Apps modernas |
| **SendGrid** | 100/día | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Empresarial |
| **Amazon SES** | Pay-as-you-go | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Alto volumen |

---

## 🎯 Recomendación Final

**Para tu proyecto, recomiendo Brevo porque:**

1. ✅ Plan gratuito generoso (300/día es suficiente para empezar)
2. ✅ Muy fácil de implementar
3. ✅ Buena entregabilidad
4. ✅ Analytics incluidos
5. ✅ Escalable cuando crezcas

**Cuando necesites más:**
- Si superas 300/día → Plan Lite ($25/mes) = 10,000/mes
- Si superas 10,000/mes → Considera Amazon SES o SendGrid

---

## 🔐 Variables de Entorno

Agrega a tu `.env`:

```env
BREVO_API_KEY=tu_api_key_aqui
```

---

## 📝 Notas Importantes

1. **Autenticación de dominio:** Para mejorar la entregabilidad, configura SPF y DKIM en tu dominio
2. **Templates:** Brevo permite crear templates HTML profesionales
3. **Rate limiting:** Respeta los límites del plan para evitar bloqueos
4. **Testing:** Usa el modo sandbox de Brevo para pruebas

---

## 🚨 Alternativa: Supabase Edge Functions

Si prefieres mantener todo en Supabase, puedes crear una Edge Function que use Brevo:

```typescript
// supabase/functions/send-alert/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { to, subject, html } = await req.json()
  
  const response = await fetch('https://api.brevo.com/v3/smtp/email', {
    method: 'POST',
    headers: {
      'api-key': Deno.env.get('BREVO_API_KEY')!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sender: { email: 'noreply@bullanalytics.com' },
      to: [{ email: to }],
      subject,
      htmlContent: html,
    }),
  })
  
  return new Response(JSON.stringify(await response.json()))
})
```

---

¿Necesitas ayuda implementando alguna de estas opciones?

