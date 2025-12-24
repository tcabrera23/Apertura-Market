# Modularización de Conexiones de Broker

## Resumen

Se ha refactorizado la lógica de conexiones con brokers (IOL y Binance) en módulos separados para mejorar la organización del código y facilitar el mantenimiento.

## Archivos Creados

### 1. `conexion_iol.py`
Módulo dedicado para la conexión con IOL (InvertirOnline).

**Clase principal:**
- `ConexionIOL`: Maneja autenticación y obtención de portfolio desde IOL

**Métodos principales:**
- `autenticar()`: Autentica con IOL y obtiene access token
- `obtener_portfolio()`: Obtiene el portfolio del usuario
- `validar_credenciales()`: Valida que las credenciales sean correctas
- `obtener_info()`: Obtiene información sobre la conexión

**Funciones de compatibilidad:**
- `get_iol_access_token()`: Función legacy para compatibilidad
- `get_iol_portfolio()`: Función legacy para compatibilidad

### 2. `conexion_binance.py`
Módulo dedicado para la conexión con Binance.

**Clase principal:**
- `ConexionBinance`: Maneja autenticación y obtención de portfolio desde Binance

**Métodos principales:**
- `validar_credenciales()`: Valida las credenciales de API
- `obtener_portfolio()`: Obtiene el portfolio del usuario
- `obtener_info()`: Obtiene información sobre la conexión
- `_generar_firma()`: Genera firma HMAC para autenticación
- `_obtener_precios()`: Obtiene precios actuales de Binance

**Funciones de compatibilidad:**
- `get_binance_portfolio()`: Función legacy para compatibilidad

## Cambios en `app_supabase.py`

### Importaciones actualizadas:
```python
from conexion_iol import ConexionIOL, get_iol_access_token, get_iol_portfolio
from conexion_binance import ConexionBinance, get_binance_portfolio
```

### Endpoints actualizados:

1. **`POST /api/broker-connections`**: 
   - Ahora usa `ConexionIOL.validar_credenciales()` para IOL
   - Ahora usa `ConexionBinance.validar_credenciales()` para Binance

2. **`GET /api/broker-connections/{connection_id}/portfolio`**:
   - Ahora usa `ConexionIOL.obtener_portfolio()` para IOL
   - Ahora usa `ConexionBinance.obtener_portfolio()` para Binance

## Tests Actualizados

Se agregaron tests completos en `test_all.py`:

### Tests Unitarios:
- `TestConexionIOL`: Tests de inicialización, autenticación y obtención de portfolio
- `TestConexionBinance`: Tests de inicialización, validación de credenciales y obtención de portfolio

### Tests de Integración:
- `TestBrokerConnectionsAPI`: Tests de los endpoints de API para crear conexiones y obtener portfolios

## Ventajas de la Modularización

1. **Separación de responsabilidades**: Cada broker tiene su propio módulo
2. **Facilidad de mantenimiento**: Cambios en un broker no afectan al otro
3. **Testabilidad**: Cada módulo puede ser testeado independientemente
4. **Extensibilidad**: Fácil agregar nuevos brokers siguiendo el mismo patrón
5. **Reutilización**: Las clases pueden ser usadas directamente sin pasar por la API

## Compatibilidad

Se mantienen las funciones legacy (`get_iol_access_token`, `get_iol_portfolio`, `get_binance_portfolio`) para compatibilidad con código existente, pero se recomienda usar las clases directamente en nuevo código.

## Uso Recomendado

### Para IOL:
```python
from conexion_iol import ConexionIOL

conexion = ConexionIOL(username, password)
if await conexion.autenticar():
    portfolio = await conexion.obtener_portfolio()
```

### Para Binance:
```python
from conexion_binance import ConexionBinance

conexion = ConexionBinance(api_key, api_secret)
if await conexion.validar_credenciales():
    portfolio = await conexion.obtener_portfolio()
```

## Archivo Legacy

El archivo `broker_clients.py` se mantiene por compatibilidad, pero se recomienda usar los nuevos módulos `conexion_iol.py` y `conexion_binance.py` en nuevo código.

