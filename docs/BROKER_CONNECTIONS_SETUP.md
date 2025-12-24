# Configuración de Conexiones de Broker

Esta guía explica cómo configurar la funcionalidad de conexiones de broker (IOL y Binance) para usuarios premium.

## Requisitos Previos

1. Usuario con suscripción activa (plan Plus o Pro)
2. Tabla `broker_connections` en Supabase
3. Variable de entorno `ENCRYPTION_KEY` configurada
4. Dependencias Python instaladas:
   - `cryptography`
   - `requests`

## 1. Crear Tabla en Supabase

Ejecuta el siguiente SQL en el editor SQL de Supabase:

```sql
-- Create broker_connections table
CREATE TABLE IF NOT EXISTS broker_connections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    broker_name VARCHAR(50) NOT NULL CHECK (broker_name IN ('IOL', 'BINANCE')),
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    username_encrypted TEXT,
    password_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_synced TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, broker_name)
);

-- Add indexes for better performance
CREATE INDEX idx_broker_connections_user_id ON broker_connections(user_id);
CREATE INDEX idx_broker_connections_broker_name ON broker_connections(broker_name);
CREATE INDEX idx_broker_connections_is_active ON broker_connections(is_active);

-- Enable Row Level Security
ALTER TABLE broker_connections ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Users can only see their own connections
CREATE POLICY "Users can view own broker connections"
    ON broker_connections FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own connections
CREATE POLICY "Users can create own broker connections"
    ON broker_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own connections
CREATE POLICY "Users can update own broker connections"
    ON broker_connections FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own connections
CREATE POLICY "Users can delete own broker connections"
    ON broker_connections FOR DELETE
    USING (auth.uid() = user_id);

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_broker_connections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_broker_connections_timestamp
    BEFORE UPDATE ON broker_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_broker_connections_updated_at();
```

## 2. Configurar Variables de Entorno

Agrega la siguiente variable al archivo `.env`:

```bash
# Encryption key for broker API credentials (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your_encryption_key_here
```

Para generar una clave de encriptación:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 3. Instalar Dependencias

Si no está ya instalada, agrega `cryptography` al `requirements.txt`:

```bash
pip install cryptography
```

## 4. Configurar API Keys en los Brokers

### InvertirOnline (IOL)

1. Inicia sesión en https://www.invertironline.com
2. Ve a "Mi Cuenta" > "Personalización" > "APIs"
3. Acepta los términos y condiciones del servicio
4. Envía un mensaje solicitando la activación de APIs
5. Una vez activado, usa tus credenciales de IOL en la aplicación

### Binance

1. Inicia sesión en https://www.binance.com
2. Ve a "Perfil" > "API Management"
3. Crea una nueva API Key
4. Configura los permisos:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ **NO habilites** "Enable Withdrawals"
5. Guarda la API Key y Secret Key de forma segura
6. Configura IP whitelist si es necesario (recomendado)

## 5. Uso de la Funcionalidad

### Para Usuarios

1. Inicia sesión en BullAnalytics
2. Ve al Dashboard
3. Haz clic en la pestaña "Broker" (visible solo para usuarios Plus/Pro)
4. Haz clic en "Conectar Broker"
5. Selecciona el broker (IOL o Binance)
6. Ingresa las credenciales correspondientes:
   - **IOL**: Usuario y contraseña
   - **Binance**: API Key y API Secret
7. Haz clic en "Conectar"
8. Una vez conectado, tu portafolio se sincronizará automáticamente

### Características

- **Sincronización Automática**: Al conectar un broker, el portafolio se carga automáticamente
- **Sincronización Manual**: Puedes sincronizar manualmente en cualquier momento
- **Múltiples Brokers**: Conecta tanto IOL como Binance simultáneamente
- **Seguridad**: Las credenciales se almacenan encriptadas en la base de datos
- **Permisos Limitados**: Solo lectura y trading, sin permisos de retiro

### Endpoints API

#### Crear Conexión
```
POST /api/broker-connections
Authorization: Bearer {token}
Content-Type: application/json

{
  "broker_name": "IOL|BINANCE",
  "username": "string",      // Solo IOL
  "password": "string",      // Solo IOL
  "api_key": "string",       // Binance
  "api_secret": "string"     // Binance
}
```

#### Listar Conexiones
```
GET /api/broker-connections
Authorization: Bearer {token}
```

#### Obtener Portafolio
```
GET /api/broker-connections/{connection_id}/portfolio
Authorization: Bearer {token}
```

#### Eliminar Conexión
```
DELETE /api/broker-connections/{connection_id}
Authorization: Bearer {token}
```

## Seguridad

### Encriptación
- Las credenciales se encriptan usando Fernet (criptografía simétrica)
- La clave de encriptación debe mantenerse segura y nunca exponerse

### Permisos de Broker
- **IOL**: Solo se usa para lectura de portafolio (GET)
- **Binance**: Solo permisos de lectura y trading, **NUNCA** de retiro

### Row Level Security (RLS)
- Los usuarios solo pueden acceder a sus propias conexiones
- Las políticas de Supabase garantizan el aislamiento de datos

## Troubleshooting

### Error: "Broker connections require an active paid subscription"
- Verifica que el usuario tenga una suscripción activa (Plus o Pro)
- Revisa la tabla `subscriptions` en Supabase

### Error: "Failed to authenticate with IOL/Binance"
- Verifica que las credenciales sean correctas
- Para IOL: Asegúrate de tener las APIs activadas
- Para Binance: Verifica que la API Key tenga los permisos correctos

### Error: "ENCRYPTION_KEY environment variable is required"
- Configura la variable `ENCRYPTION_KEY` en el archivo `.env`
- Genera una nueva clave usando el comando proporcionado arriba

### Portafolio no se muestra
- Verifica que la conexión esté activa (`is_active = true`)
- Sincroniza manualmente usando el botón "Sincronizar Ahora"
- Revisa los logs del servidor para más detalles

## Notas Importantes

1. **Seguridad de Credenciales**: Nunca compartas tus credenciales de broker con nadie
2. **Permisos de API**: Siempre limita los permisos de API al mínimo necesario
3. **Monitoreo**: Revisa regularmente la actividad de tu cuenta en los brokers
4. **Backup de Claves**: Guarda de forma segura tu `ENCRYPTION_KEY` - si la pierdes, no podrás descifrar las credenciales almacenadas
5. **Testing**: Usa cuentas de prueba/sandbox cuando estén disponibles

## Referencias

- [API de IOL](https://api.invertironline.com/)
- [API de Binance](https://binance-docs.github.io/apidocs/spot/en/)
- [Cryptography Library](https://cryptography.io/)



