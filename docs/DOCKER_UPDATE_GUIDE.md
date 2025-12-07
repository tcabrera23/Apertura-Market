# 🔄 Guía de Actualización - Docker

Esta guía explica cómo actualizar tu aplicación cuando hay cambios en GitHub.

---

## 📋 Proceso de Actualización

Cuando actualizas el código desde GitHub, **NO es suficiente solo reiniciar el contenedor**. Necesitas seguir estos pasos:

### ⚠️ ¿Por qué no solo reiniciar?

- **Reiniciar (`docker compose restart`)**: Solo reinicia el contenedor con la misma imagen antigua. No carga los nuevos archivos.
- **Recrear (`docker compose up -d --build`)**: Reconstruye la imagen con el nuevo código y crea un nuevo contenedor.

---

## 🚀 Método 1: Usando el Script de Despliegue (Recomendado)

El script `deploy.sh` ya incluye un comando `update` que hace todo automáticamente:

```bash
cd /opt/bullanalytics
./deploy.sh update
```

Este comando:
1. ✅ Hace `git pull` para obtener el último código
2. ✅ Reconstruye la imagen Docker con el nuevo código
3. ✅ Detiene el contenedor antiguo
4. ✅ Crea un nuevo contenedor con la nueva imagen
5. ✅ Verifica que todo funcione

---

## 🛠️ Método 2: Manual (Paso a Paso)

Si prefieres hacerlo manualmente:

### Paso 1: Actualizar el código

```bash
cd /opt/bullanalytics
git pull origin main
# O si tu rama es master:
# git pull origin master
```

### Paso 2: Reconstruir la imagen

```bash
docker compose build
```

**Nota:** Esto puede tardar varios minutos la primera vez, pero las siguientes veces será más rápido gracias al cache de Docker.

### Paso 3: Recrear el contenedor

```bash
docker compose up -d
```

El flag `-d` ejecuta en segundo plano. Docker Compose automáticamente:
- Detiene el contenedor antiguo
- Crea uno nuevo con la nueva imagen
- Mantiene los mismos volúmenes y configuración

### Paso 4: Verificar

```bash
# Ver logs para asegurarte de que inició correctamente
docker compose logs -f

# Verificar health check
curl http://localhost:8080/health
```

---

## 🔄 Método 3: Todo en un Comando

Puedes hacer todo en una sola línea:

```bash
cd /opt/bullanalytics && \
git pull origin main && \
docker compose up -d --build
```

Esto:
- Actualiza el código
- Reconstruye la imagen
- Recrea el contenedor

---

## 📊 Diferencia entre Comandos

### `docker compose restart`
```bash
docker compose restart
```
- ❌ **NO actualiza el código**
- ✅ Solo reinicia el contenedor existente
- ⚡ Rápido (segundos)
- 🎯 Útil para: Reiniciar después de cambios en `.env` o errores temporales

### `docker compose up -d`
```bash
docker compose up -d
```
- ✅ Recrea el contenedor si hay cambios en `docker-compose.yml`
- ❌ **NO reconstruye la imagen** (usa la imagen existente)
- ⚡ Rápido (segundos)
- 🎯 Útil para: Cambios en configuración de Docker Compose

### `docker compose up -d --build`
```bash
docker compose up -d --build
```
- ✅ Reconstruye la imagen con el nuevo código
- ✅ Recrea el contenedor con la nueva imagen
- ⏱️ Tarda más (minutos, depende del tamaño)
- 🎯 Útil para: **Actualizar código de la aplicación**

### `docker compose build && docker compose up -d`
```bash
docker compose build && docker compose up -d
```
- ✅ Igual que `--build`, pero en dos pasos
- ✅ Te permite ver si el build falla antes de recrear
- 🎯 Útil para: Debugging o cuando quieres ver el proceso paso a paso

---

## 🔍 Verificar Cambios

Después de actualizar, verifica que los cambios se aplicaron:

### 1. Ver la versión del código

```bash
# Ver el último commit
git log -1

# Ver qué archivos cambiaron
git diff HEAD~1 HEAD
```

### 2. Verificar que el contenedor tiene el nuevo código

```bash
# Ver la fecha de modificación de un archivo dentro del contenedor
docker compose exec bullanalytics-api ls -la app_supabase.py

# O ver el contenido de un archivo específico
docker compose exec bullanalytics-api head -20 app_supabase.py
```

### 3. Verificar que la aplicación funciona

```bash
# Health check
curl http://localhost:8080/health

# Probar un endpoint
curl http://localhost:8080/api/tracking-assets
```

---

## ⚡ Optimización: Cache de Docker

Docker usa cache para acelerar los builds. Si solo cambiaste código Python (no dependencias), el build será rápido porque:

- ✅ Las capas de dependencias se reutilizan
- ✅ Solo se reconstruye la capa con tu código

**Para forzar un build completo sin cache:**

```bash
docker compose build --no-cache
```

Esto es útil si:
- Cambiaste `requirements.txt`
- Tienes problemas raros que sospechas vienen del cache
- Quieres asegurarte de que todo se reconstruye desde cero

---

## 🐛 Troubleshooting de Actualizaciones

### Problema: "El contenedor no inicia después de actualizar"

```bash
# Ver logs detallados
docker compose logs --tail=100

# Verificar que el código se actualizó
git log -1

# Reconstruir sin cache
docker compose build --no-cache
docker compose up -d
```

### Problema: "Los cambios no se reflejan"

1. **Verifica que hiciste pull:**
   ```bash
   git status
   git log -1
   ```

2. **Verifica que reconstruiste:**
   ```bash
   docker images | grep bullanalytics
   # La fecha de creación debe ser reciente
   ```

3. **Fuerza recreación:**
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

### Problema: "Error al hacer git pull"

```bash
# Si hay conflictos locales
git stash
git pull origin main
git stash pop

# Si hay cambios no commiteados que quieres descartar
git reset --hard
git pull origin main
```

---

## 📝 Checklist de Actualización

Antes de actualizar en producción:

- [ ] Hacer backup del código actual (opcional pero recomendado)
- [ ] Revisar los cambios en GitHub antes de hacer pull
- [ ] Verificar que no hay cambios locales importantes sin commitear
- [ ] Hacer pull del código
- [ ] Reconstruir la imagen
- [ ] Verificar logs después de recrear
- [ ] Probar endpoints críticos
- [ ] Verificar health check

---

## 🎯 Resumen Rápido

**Para actualizar código desde GitHub:**

```bash
cd /opt/bullanalytics
./deploy.sh update
```

**O manualmente:**

```bash
cd /opt/bullanalytics
git pull origin main
docker compose up -d --build
```

**Para solo reiniciar (sin actualizar código):**

```bash
docker compose restart
```

---

## 💡 Tips

1. **Actualiza fuera de horas pico** para minimizar impacto
2. **Mantén un backup** del código anterior (Git ya lo hace con historial)
3. **Monitorea los logs** después de cada actualización
4. **Prueba en staging primero** si tienes un ambiente de pruebas
5. **Usa tags de Git** para versionar tus releases

---

## 🔗 Comandos Relacionados

```bash
# Ver estado actual
./deploy.sh status

# Ver logs en tiempo real
./deploy.sh logs

# Ver qué cambió en el último commit
git show HEAD

# Ver diferencias entre local y remoto
git fetch
git diff HEAD origin/main
```

---

¡Ahora sabes cómo actualizar tu aplicación correctamente! 🚀

