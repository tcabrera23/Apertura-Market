# Tests Consolidados

## Descripción

Todos los tests del proyecto han sido consolidados en un solo archivo `test_all.py` en la raíz del proyecto para facilitar la automatización con GitHub Actions.

## Estructura

El archivo `test_all.py` contiene:

- **Fixtures**: Todas las fixtures necesarias para los tests (client, mock_user, mock_supabase, etc.)
- **Tests de Reglas (Rules)**: CRUD operations y validaciones
- **Tests de Watchlists**: Gestión de listas de seguimiento
- **Tests de Cupones (Coupons)**: Validación de cupones de descuento
- **Tests de Email**: Integración con Brevo y templates de email
- **Tests de Integración**: Flujos completos de usuario

## Ejecutar Tests Localmente

### Ejecutar todos los tests:
```bash
pytest test_all.py -v
```

### Ejecutar solo tests unitarios:
```bash
pytest test_all.py -v -m unit
```

### Ejecutar solo tests de integración:
```bash
pytest test_all.py -v -m integration
```

### Ejecutar con cobertura:
```bash
pytest test_all.py -v --cov=app_supabase --cov-report=html
```

## GitHub Actions

Los tests se ejecutan automáticamente en GitHub Actions cuando:
- Se hace push a las ramas `main`, `master` o `develop`
- Se crea un Pull Request a estas ramas
- Se ejecuta manualmente desde la pestaña Actions

El workflow está configurado en `.github/workflows/tests.yml` y ejecuta los tests en Python 3.10, 3.11 y 3.12.

## Variables de Entorno para Tests

Los tests usan variables de entorno de prueba que se configuran automáticamente en el archivo `test_all.py`. Para GitHub Actions, puedes configurar secrets opcionales:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY`
- `SUPABASE_JWT_SECRET`
- `BREVO_API_KEY`

Si no se configuran, se usan valores de prueba por defecto.

## Archivos Originales

Los tests originales se mantienen en la carpeta `tests/`:
- `tests/test_coupons.py`
- `tests/test_email_integration.py`
- `tests/test_integration.py`
- `tests/test_rules.py`
- `tests/test_watchlists.py`
- `tests/conftest.py`

Estos archivos pueden seguir usándose si prefieres mantener los tests separados, pero el archivo consolidado `test_all.py` es el recomendado para CI/CD.

