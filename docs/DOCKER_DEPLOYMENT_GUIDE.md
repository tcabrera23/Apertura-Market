# 🐳 Guía de Despliegue con Docker - BullAnalytics API

Esta guía te ayudará a desplegar `app_supabase.py` en tu VPS usando Docker.

---

## 📋 Prerrequisitos

### 1. VPS con:
- Ubuntu 20.04+ o Debian 11+
- Acceso root o usuario con sudo
- Mínimo 2GB RAM, 2 CPU cores
- 20GB espacio en disco

### 2. Software necesario:
- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)
- Git

---

## 🚀 Paso 1: Preparar el VPS

### 1.1 Conectarse al VPS

```bash
ssh root@tu-vps-ip
# O con usuario
ssh usuario@tu-vps-ip
```

### 1.2 Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker (si no eres root)
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker compose version
```

### 1.4 Instalar Git (si no está instalado)

```bash
sudo apt install git -y
```

---

## 📦 Paso 2: Clonar el Repositorio

### 2.1 Crear directorio para la aplicación

```bash
mkdir -p /opt/bullanalytics
cd /opt/bullanalytics
```

### 2.2 Clonar el repositorio

```bash
# Si tienes el código en Git
git clone https://github.com/tu-usuario/finance_portfolio.git .

# O si prefieres subir los archivos manualmente:
# Usa SCP o SFTP para subir los archivos necesarios
```

### 2.3 Verificar archivos necesarios

Asegúrate de tener estos archivos en el directorio:
- `app_supabase.py`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- Archivos HTML, CSS, JS, imágenes, etc.

---

## 🔐 Paso 3: Configurar Variables de Entorno

### 3.1 Crear archivo .env

```bash
cd /opt/bullanalytics
cp .env.example .env
nano .env
```

### 3.2 Editar .env con tus credenciales

```bash
# Supabase Configuration
SUPABASE_URL=https://pwumamzbicapuiqkwrey.supabase.co
SUPABASE_SERVICE_KEY=tu_service_key_aqui
SUPABASE_ANON_KEY=tu_anon_key_aqui
SUPABASE_JWT_SECRET=tu_jwt_secret_aqui

# Brevo Email Configuration
BREVO_API_KEY=tu_brevo_api_key_aqui

# PayPal Configuration
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=tu_paypal_client_id
PAYPAL_CLIENT_SECRET=tu_paypal_client_secret
PAYPAL_RETURN_URL=https://bullanalytics.io/subscription-success.html
PAYPAL_CANCEL_URL=https://bullanalytics.io/pricing.html

# CORS Configuration
CORS_ORIGINS=https://bullanalytics.io,http://localhost:8080

# Frontend URL
FRONTEND_URL=https://bullanalytics.io

# Groq API
GROQ_API_KEY=tu_groq_api_key_aqui
```

### 3.3 Proteger el archivo .env

```bash
chmod 600 .env
```

---

## 🏗️ Paso 4: Construir y Ejecutar con Docker

### 4.1 Construir la imagen

```bash
cd /opt/bullanalytics
docker compose build
```

Esto puede tardar varios minutos la primera vez.

### 4.2 Verificar que la imagen se construyó

```bash
docker images | grep bullanalytics
```

### 4.3 Iniciar el contenedor

```bash
docker compose up -d
```

El flag `-d` ejecuta el contenedor en modo detached (en segundo plano).

### 4.4 Verificar que el contenedor está corriendo

```bash
docker compose ps
```

Deberías ver algo como:
```
NAME                  STATUS          PORTS
bullanalytics-api     Up 2 minutes    0.0.0.0:8080->8080/tcp
```

### 4.5 Ver los logs

```bash
# Ver logs en tiempo real
docker compose logs -f

# Ver últimas 100 líneas
docker compose logs --tail=100
```

---

## ✅ Paso 5: Verificar que Funciona

### 5.1 Health Check

```bash
curl http://localhost:8080/health
```

Deberías recibir:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 5.2 Probar endpoint público

```bash
curl http://localhost:8080/api/tracking-assets
```

### 5.3 Verificar desde el navegador

Abre en tu navegador:
```
http://tu-vps-ip:8080
```

---

## 🌐 Paso 6: Configurar Nginx como Reverse Proxy (Recomendado)

### 6.1 Instalar Nginx

```bash
sudo apt install nginx -y
```

### 6.2 Crear configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/bullanalytics
```

Pega esta configuración:

```nginx
server {
    listen 80;
    server_name bullanalytics.io www.bullanalytics.io;

    # Redirigir HTTP a HTTPS (después de configurar SSL)
    # return 301 https://$server_name$request_uri;

    # Por ahora, proxy a la aplicación
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 6.3 Habilitar el sitio

```bash
sudo ln -s /etc/nginx/sites-available/bullanalytics /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl restart nginx
```

### 6.4 Configurar SSL con Certbot (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL
sudo certbot --nginx -d bullanalytics.io -d www.bullanalytics.io

# Renovar automáticamente (se configura automáticamente)
sudo certbot renew --dry-run
```

Después de obtener el certificado, actualiza la configuración de Nginx para usar HTTPS.

---

## 🔥 Paso 7: Configurar Firewall

### 7.1 Configurar UFW (Ubuntu Firewall)

```bash
# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP
sudo ufw allow 80/tcp

# Permitir HTTPS
sudo ufw allow 443/tcp

# Opcional: Permitir puerto 8080 directamente (si no usas Nginx)
# sudo ufw allow 8080/tcp

# Habilitar firewall
sudo ufw enable

# Verificar estado
sudo ufw status
```

---

## 🔄 Paso 8: Gestión del Contenedor

### 8.1 Comandos útiles

```bash
# Detener el contenedor
docker compose down

# Iniciar el contenedor
docker compose up -d

# Reiniciar el contenedor
docker compose restart

# Ver logs
docker compose logs -f

# Ver logs de los últimos 100 líneas
docker compose logs --tail=100

# Reconstruir después de cambios
docker compose up -d --build

# Detener y eliminar contenedor (mantiene volúmenes)
docker compose down

# Detener y eliminar todo (incluyendo volúmenes)
docker compose down -v
```

### 8.2 Actualizar la aplicación

**⚠️ IMPORTANTE:** No es suficiente solo reiniciar. Necesitas reconstruir la imagen.

**Opción 1: Usando el script (Recomendado)**
```bash
cd /opt/bullanalytics
./deploy.sh update
```

**Opción 2: Manualmente**
```bash
cd /opt/bullanalytics

# 1. Actualizar código desde GitHub
git pull origin main

# 2. Reconstruir imagen y recrear contenedor
docker compose up -d --build
```

**¿Por qué `--build`?**
- `docker compose restart` solo reinicia el contenedor (no carga nuevo código)
- `docker compose up -d --build` reconstruye la imagen con el nuevo código y recrea el contenedor

**Ver guía completa de actualizaciones:** `docs/DOCKER_UPDATE_GUIDE.md`

---

## 📊 Paso 9: Monitoreo y Logs

### 9.1 Ver logs en tiempo real

```bash
docker compose logs -f bullanalytics-api
```

### 9.2 Ver uso de recursos

```bash
docker stats bullanalytics-api
```

### 9.3 Configurar rotación de logs

Docker Compose ya está configurado para rotar logs (ver `docker-compose.yml`):
- Máximo 10MB por archivo
- Máximo 3 archivos

---

## 🛠️ Paso 10: Troubleshooting

### 10.1 El contenedor no inicia

```bash
# Ver logs detallados
docker compose logs bullanalytics-api

# Verificar configuración
docker compose config

# Verificar que el puerto no esté en uso
sudo netstat -tulpn | grep 8080
```

### 10.2 Error de conexión a Supabase

- Verifica que las variables de entorno estén correctas
- Verifica que el VPS tenga acceso a internet
- Verifica los logs: `docker compose logs | grep -i supabase`

### 10.3 Error de permisos

```bash
# Asegúrate de que los archivos tengan los permisos correctos
sudo chown -R $USER:$USER /opt/bullanalytics
chmod 600 .env
```

### 10.4 El contenedor se reinicia constantemente

```bash
# Ver logs para identificar el error
docker compose logs --tail=200

# Verificar recursos del sistema
docker stats bullanalytics-api
free -h
df -h
```

---

## 🔒 Paso 11: Seguridad Adicional

### 11.1 Actualizar Docker regularmente

```bash
sudo apt update
sudo apt upgrade docker.io docker-compose
```

### 11.2 No exponer el puerto 8080 directamente

Si usas Nginx, no necesitas exponer el puerto 8080 al exterior. Modifica `docker-compose.yml`:

```yaml
ports:
  - "127.0.0.1:8080:8080"  # Solo accesible desde localhost
```

### 11.3 Backup del archivo .env

```bash
# Crear backup
cp .env .env.backup

# Guardar en lugar seguro
```

---

## 📈 Paso 12: Optimizaciones (Opcional)

### 12.1 Aumentar workers de Uvicorn

Si tu VPS tiene más recursos, puedes aumentar los workers. Edita el `Dockerfile`:

```dockerfile
CMD ["uvicorn", "app_supabase:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

Ajusta el número de workers según tus CPU cores (generalmente: workers = CPU cores * 2 + 1).

### 12.2 Configurar límites de recursos

En `docker-compose.yml`, agrega:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

---

## 🎯 Resumen de Comandos Rápidos

```bash
# Iniciar
cd /opt/bullanalytics && docker compose up -d

# Ver logs
docker compose logs -f

# Reiniciar
docker compose restart

# Actualizar
git pull && docker compose up -d --build

# Detener
docker compose down

# Ver estado
docker compose ps
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker compose logs`
2. Verifica las variables de entorno: `cat .env`
3. Verifica la conectividad: `curl http://localhost:8080/health`
4. Revisa los recursos: `docker stats`

---

## ✅ Checklist de Despliegue

- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado en `/opt/bullanalytics`
- [ ] Archivo `.env` configurado con todas las credenciales
- [ ] Imagen Docker construida exitosamente
- [ ] Contenedor corriendo (`docker compose ps`)
- [ ] Health check responde correctamente
- [ ] Nginx configurado como reverse proxy
- [ ] SSL configurado con Let's Encrypt
- [ ] Firewall configurado
- [ ] Logs funcionando correctamente
- [ ] Backup del archivo `.env` creado

---

¡Tu aplicación debería estar funcionando ahora! 🎉

