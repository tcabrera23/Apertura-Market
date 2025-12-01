# Guía de Templates de Email - BullAnalytics

## 📧 ¿Dónde guardar los templates de email?

### ✅ **Recomendación: Templates en el código (Python)**

**Ventajas:**
- ✅ **Versionado con Git**: Todos los cambios están en el repositorio
- ✅ **Control total**: Puedes personalizar completamente el HTML/CSS
- ✅ **Fácil de testear**: Puedes probar cambios localmente
- ✅ **Sin dependencias externas**: No necesitas acceder a otra plataforma
- ✅ **Rápido**: No hay llamadas adicionales a APIs
- ✅ **Mantenible**: Todo el código en un solo lugar

**Desventajas:**
- ❌ Requiere deploy para cambios
- ❌ No hay editor visual (pero puedes usar HTML)

**Ideal para:** Templates que no cambian frecuentemente, correos transaccionales, alertas

---

### ❌ **NO recomendado: Templates en Supabase**

**Razones:**
- ❌ No está diseñado para almacenar HTML complejo
- ❌ Difícil de mantener y versionar
- ❌ No hay editor visual
- ❌ Agrega complejidad innecesaria

---

### ⚠️ **Opcional: Templates en Brevo (para casos especiales)**

**Ventajas:**
- ✅ Editor visual en el dashboard de Brevo
- ✅ Cambios sin deploy (útil para marketing)
- ✅ Analytics integrados
- ✅ A/B testing

**Desventajas:**
- ❌ Requiere llamadas adicionales a la API de Brevo
- ❌ Menos control sobre el código
- ❌ No está versionado en Git
- ❌ Más lento (llamada extra a API)

**Ideal para:** Campañas de marketing, emails promocionales que cambian frecuentemente

---

## 🎯 **Estrategia Recomendada para BullAnalytics**

### **Templates en código Python** (`email_templates.py`)

Usa templates en código para:
- ✅ **Onboarding/Bienvenida** → Se envía al registrarse
- ✅ **Alertas financieras** → Se envía cuando se cumple una regla
- ✅ **Confirmación de suscripción** → Se envía al suscribirse
- ✅ **Reset de contraseña** → Se envía al solicitar reset
- ✅ **Notificaciones transaccionales** → Cualquier email automático

### **Templates en Brevo** (opcional, futuro)

Usa templates de Brevo solo para:
- 📧 Campañas de marketing masivas
- 📧 Newsletters
- 📧 Promociones especiales

---

## 📁 Estructura de Archivos

```
finance_portfolio/
├── email_templates.py          # ✅ Templates principales (recomendado)
├── app_supabase.py             # Backend que usa los templates
└── templates/                   # (Opcional) Si tienes muchos templates
    ├── onboarding.html
    ├── alerts.html
    └── ...
```

---

## 🔍 **Cómo verificar que funciona correctamente**

### 1. **Logs del servidor** ✅ (Ya lo tienes)
```
✅ Email enviado exitosamente a tomascabrera739@gmail.com: <message_id>
```

### 2. **Dashboard de Brevo** 📊
1. Ve a [app.brevo.com](https://app.brevo.com)
2. **Statistics** → **Email Activity**
3. Verás:
   - ✅ Emails enviados
   - ✅ Emails entregados
   - ✅ Emails abiertos
   - ✅ Emails con clics
   - ⚠️ Rebotes
   - ⚠️ Spam reports

### 3. **API Response** ✅
El endpoint devuelve:
```json
{
  "message": "Email enviado exitosamente",
  "message_id": "<202512011752.14437573939@smtp-relay.mailin.fr>",
  "to": "tomascabrera739@gmail.com"
}
```

### 4. **Verificar en tu bandeja de entrada**
- ⏱️ Puede tardar 1-5 minutos
- 📁 Revisa la carpeta de spam
- 🔍 Busca "BullAnalytics" o "Brevo"

---

## 🚨 **Por qué puede no llegar el email**

### **Razones comunes:**

1. **Spam/Junk Mail** 📁
   - Gmail/Outlook pueden filtrar correos de nuevos remitentes
   - **Solución**: Revisa la carpeta de spam

2. **Delay normal** ⏱️
   - Brevo puede tardar 1-5 minutos en entregar
   - **Solución**: Espera unos minutos

3. **Email inválido** ❌
   - Verifica que el email sea correcto
   - **Solución**: Prueba con otro email

4. **Límites de Brevo** 🚫
   - Plan gratuito: 300/día
   - **Solución**: Verifica en el dashboard de Brevo

5. **Dominio no verificado** ⚠️
   - Si usas un dominio personalizado, debe estar verificado
   - **Solución**: Verifica tu dominio en Brevo

---

## 📝 **Templates Disponibles**

### 1. **Onboarding/Bienvenida**
```python
from email_templates import get_onboarding_email_template

template = get_onboarding_email_template(
    user_name="Juan",
    user_email="juan@example.com"
)

send_alert_email(
    to_email="juan@example.com",
    subject=template["subject"],
    html_content=template["html_content"]
)
```

### 2. **Alertas Financieras**
```python
from email_templates import get_alert_email_template

template = get_alert_email_template(
    rule_name="Alerta NVDA",
    ticker="NVDA",
    alert_message="NVDA está por debajo de $500",
    current_price=495.50,
    threshold=500.00,
    rule_type="price_below"
)
```

### 3. **Reset de Contraseña**
```python
from email_templates import get_password_reset_email_template

template = get_password_reset_email_template(
    reset_link="https://bullanalytics.com/reset?token=abc123",
    user_name="Juan"
)
```

### 4. **Confirmación de Suscripción**
```python
from email_templates import get_subscription_confirmation_email_template

template = get_subscription_confirmation_email_template(
    plan_name="Plus",
    price=29.99,
    billing_period="mensual"
)
```

---

## 🎨 **Personalizar Templates**

### **Editar un template existente:**
1. Abre `email_templates.py`
2. Modifica la función del template que necesites
3. Cambia HTML, CSS, colores, textos
4. Reinicia el servidor

### **Crear un nuevo template:**
1. Agrega una nueva función en `email_templates.py`:
```python
def get_mi_nuevo_template(param1: str, param2: str) -> Dict[str, str]:
    subject = "Mi Asunto"
    html_content = f"""
    <html>...</html>
    """
    return {"subject": subject, "html_content": html_content}
```

2. Importa y usa en `app_supabase.py`:
```python
from email_templates import get_mi_nuevo_template
```

---

## 🔄 **Flujo Completo de Email**

```
Usuario se registra
    ↓
ensure_user_persisted() crea usuario
    ↓
get_onboarding_email_template() genera HTML
    ↓
send_alert_email() envía a Brevo
    ↓
Brevo procesa y entrega
    ↓
Usuario recibe email (1-5 min)
```

---

## 📊 **Monitoreo y Analytics**

### **En Brevo Dashboard:**
- **Statistics** → Ver todos los emails enviados
- **Email Activity** → Ver estado de cada email
- **Bounces** → Ver emails rebotados
- **Spam Reports** → Ver quejas de spam

### **En tu código:**
- Logs del servidor muestran cada envío
- `message_id` para tracking
- Manejo de errores con try/catch

---

## ✅ **Checklist de Verificación**

- [ ] Email se envía (200 OK en logs)
- [ ] Message ID generado por Brevo
- [ ] Aparece en Brevo Dashboard
- [ ] Email llega a la bandeja (o spam)
- [ ] Template se renderiza correctamente
- [ ] Links funcionan
- [ ] Responsive en móvil

---

## 🚀 **Próximos Pasos**

1. ✅ Templates creados en `email_templates.py`
2. ✅ Integración con onboarding lista
3. ⏭️ Implementar `check_and_send_alerts()` para alertas automáticas
4. ⏭️ Configurar cron job para verificar reglas cada 15 minutos
5. ⏭️ (Opcional) Verificar dominio en Brevo para mejor entregabilidad

---

¿Necesitas ayuda con algo más de los templates?

