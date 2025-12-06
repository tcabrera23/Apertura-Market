#!/bin/bash

# Script de despliegue para BullAnalytics API
# Uso: ./deploy.sh [comando]
# Comandos: build, start, stop, restart, logs, update, status

set -e

COMPOSE_FILE="docker-compose.yml"
PROJECT_DIR="/opt/bullanalytics"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
check_directory() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "No se encontró $COMPOSE_FILE. Asegúrate de estar en el directorio correcto."
        exit 1
    fi
}

# Verificar que existe .env
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning "No se encontró archivo .env"
        print_info "Creando .env desde .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Por favor, edita .env con tus credenciales antes de continuar."
            exit 1
        else
            print_error "No se encontró .env.example. Crea el archivo .env manualmente."
            exit 1
        fi
    fi
}

# Construir la imagen
build() {
    print_info "Construyendo imagen Docker..."
    docker compose build
    print_info "Imagen construida exitosamente."
}

# Iniciar contenedores
start() {
    print_info "Iniciando contenedores..."
    docker compose up -d
    print_info "Contenedores iniciados."
    sleep 2
    status
}

# Detener contenedores
stop() {
    print_info "Deteniendo contenedores..."
    docker compose down
    print_info "Contenedores detenidos."
}

# Reiniciar contenedores
restart() {
    print_info "Reiniciando contenedores..."
    docker compose restart
    print_info "Contenedores reiniciados."
    sleep 2
    status
}

# Ver logs
logs() {
    print_info "Mostrando logs (Ctrl+C para salir)..."
    docker compose logs -f
}

# Actualizar aplicación
update() {
    print_info "Actualizando aplicación..."
    
    # Si hay Git, hacer pull
    if [ -d ".git" ]; then
        print_info "Actualizando código desde Git..."
        git pull origin main || git pull origin master
    fi
    
    # Reconstruir y reiniciar
    print_info "Reconstruyendo imagen..."
    docker compose build
    print_info "Reiniciando contenedores..."
    docker compose up -d
    print_info "Actualización completada."
    sleep 2
    status
}

# Ver estado
status() {
    print_info "Estado de los contenedores:"
    docker compose ps
    
    print_info "\nVerificando health check..."
    sleep 3
    if curl -s http://localhost:8080/health > /dev/null; then
        print_info "✅ Aplicación está respondiendo correctamente."
        curl -s http://localhost:8080/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8080/health
    else
        print_warning "⚠️  La aplicación no está respondiendo. Revisa los logs con: ./deploy.sh logs"
    fi
}

# Verificar sistema
check_system() {
    print_info "Verificando sistema..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado."
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado."
        exit 1
    fi
    
    # Verificar que Docker está corriendo
    if ! docker info &> /dev/null; then
        print_error "Docker no está corriendo. Inicia el servicio Docker."
        exit 1
    fi
    
    print_info "✅ Sistema verificado correctamente."
}

# Mostrar ayuda
show_help() {
    echo "Script de despliegue para BullAnalytics API"
    echo ""
    echo "Uso: ./deploy.sh [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  build      - Construir la imagen Docker"
    echo "  start      - Iniciar los contenedores"
    echo "  stop       - Detener los contenedores"
    echo "  restart    - Reiniciar los contenedores"
    echo "  logs       - Ver logs en tiempo real"
    echo "  update     - Actualizar código y reiniciar"
    echo "  status     - Ver estado de los contenedores"
    echo "  check      - Verificar sistema y configuración"
    echo "  help       - Mostrar esta ayuda"
    echo ""
}

# Comando principal
main() {
    check_directory
    
    case "${1:-help}" in
        build)
            check_system
            build
            ;;
        start)
            check_system
            check_env_file
            start
            ;;
        stop)
            stop
            ;;
        restart)
            check_system
            restart
            ;;
        logs)
            logs
            ;;
        update)
            check_system
            check_env_file
            update
            ;;
        status)
            status
            ;;
        check)
            check_system
            check_env_file
            print_info "✅ Verificación completada."
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Comando desconocido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar
main "$@"

