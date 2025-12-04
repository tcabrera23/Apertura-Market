# Tests de Integración de Emails

Este documento describe los tests creados para verificar que la integración de correos electrónicos funciona correctamente, específicamente el envío de emails de onboarding cuando un usuario se registra.

## Estructura de Tests

El archivo `test_email_integration.py` contiene los siguientes grupos de tests:

### 1. TestOnboardingEmailTemplate
- **test_template_generation**: Verifica que el template de onboarding se genera correctamente con el subject y contenido HTML esperado.
- **test_template_contains_features**: Verifica que el template incluye todas las características mencionadas (listas, alertas, métricas, gráficos).

### 2. TestSendAlertEmail
- **test_send_email_success**: Verifica que el envío de email funciona correctamente cuando la API de Brevo responde exitosamente.
- **test_send_email_no_api_key**: Verifica que el sistema maneja correctamente la ausencia de `BREVO_API_KEY`.
- **test_send_email_api_exception**: Verifica el manejo de excepciones de la API de Brevo.

### 3. TestUserRegistrationEmailFlow
- **test_signup_sends_onboarding_email**: Verifica que cuando un usuario se registra, se envía automáticamente el email de onboarding con los parámetros correctos.
- **test_signup_email_template_content**: Verifica que el contenido del email de onboarding incluye la información esperada (nombre del usuario, características de BullAnalytics, etc.).
- **test_signup_email_failure_does_not_block_registration**: Verifica que si el envío de email falla, el registro del usuario aún se completa exitosamente (no bloquea el registro).
- **test_signup_with_different_email_formats**: Verifica que la extracción del nombre del usuario funciona correctamente para diferentes formatos de email.

### 4. TestEmailIntegrationEndToEnd
- **test_complete_onboarding_flow**: Test end-to-end que verifica el flujo completo desde el registro del usuario hasta la entrega del email.

## Cómo Ejecutar los Tests

### Prerrequisitos

Asegúrate de tener instaladas las dependencias:

```bash
pip install -r requirements.txt
```

Las dependencias necesarias incluyen:
- `pytest`
- `pytest-cov` (para coverage)
- `fastapi`
- `httpx` (para TestClient)
- `sib-api-v3-sdk` (SDK de Brevo)

### Ejecutar Todos los Tests de Email

```bash
pytest tests/test_email_integration.py -v
```

### Ejecutar un Test Específico

```bash
pytest tests/test_email_integration.py::TestUserRegistrationEmailFlow::test_signup_sends_onboarding_email -v
```

### Ejecutar con Coverage

```bash
pytest tests/test_email_integration.py --cov=app_supabase --cov-report=html --cov-report=term-missing
```

Esto generará un reporte de cobertura en HTML en el directorio `htmlcov/`.

### Ejecutar Todos los Tests del Proyecto

```bash
pytest tests/ -v
```

## Mocks y Fixtures

Los tests utilizan los siguientes mocks:

1. **mock_brevo_api**: Mock del cliente de la API de Brevo (`TransactionalEmailsApi`)
2. **mock_supabase_auth**: Mock de Supabase Auth para simular el registro de usuarios
3. **mock_supabase_table**: Mock de las operaciones de tabla de Supabase
4. **mock_create_default_subscription**: Mock de la función que crea la suscripción por defecto

## Verificaciones Principales

Los tests verifican que:

1. ✅ El template de onboarding se genera correctamente
2. ✅ El email se envía con los parámetros correctos (destinatario, asunto, contenido)
3. ✅ El contenido del email incluye el nombre del usuario y las características de BullAnalytics
4. ✅ El registro del usuario no falla si el envío de email falla
5. ✅ La extracción del nombre del usuario funciona para diferentes formatos de email
6. ✅ El flujo completo de registro → envío de email funciona end-to-end

## Variables de Entorno para Tests

Los tests configuran automáticamente las siguientes variables de entorno de prueba:

- `SUPABASE_URL`: URL de prueba de Supabase
- `SUPABASE_SERVICE_KEY`: Clave de servicio de prueba
- `SUPABASE_ANON_KEY`: Clave anónima de prueba
- `SUPABASE_JWT_SECRET`: Secret JWT de prueba
- `BREVO_API_KEY`: Clave API de Brevo de prueba

**Nota**: Estas variables se configuran automáticamente en los tests y no requieren configuración manual.

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'sib_api_v3_sdk'"

Instala el SDK de Brevo:
```bash
pip install sib-api-v3-sdk
```

### Error: "ModuleNotFoundError: No module named 'app_supabase'"

Asegúrate de ejecutar los tests desde el directorio raíz del proyecto:
```bash
cd /ruta/al/proyecto
pytest tests/test_email_integration.py
```

### Los tests fallan con errores de importación

Verifica que todas las dependencias estén instaladas:
```bash
pip install -r requirements.txt
```

## Integración Continua (CI)

Estos tests pueden integrarse en un pipeline de CI/CD. Ejemplo para GitHub Actions:

```yaml
name: Email Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run email tests
        run: |
          pytest tests/test_email_integration.py -v
```

## Notas Importantes

1. **Los tests no envían emails reales**: Todos los tests utilizan mocks, por lo que no se envían emails reales durante la ejecución de los tests.

2. **Tests aislados**: Cada test es independiente y no depende de otros tests.

3. **Cobertura**: Los tests cubren:
   - Generación de templates
   - Envío de emails
   - Integración con el flujo de registro
   - Manejo de errores

4. **Performance**: Los tests se ejecutan rápidamente ya que utilizan mocks en lugar de llamadas reales a APIs externas.

