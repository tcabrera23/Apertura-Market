"""
Login Starter Kit - FastAPI + Supabase
Servicio centralizado de autenticación reutilizable para múltiples aplicaciones GenAI.

Características:
- Autenticación con Email/Password
- OAuth (Google, Outlook)
- JWT Validation
- Persistencia personalizada en Supabase
- Totalmente configurable via variables de entorno
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import jwt
from supabase import create_client, Client
import uvicorn

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class Settings(BaseSettings):
    """Configuración centralizada del aplicativo"""
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str
    
    # Personalización
    user_table_name: str = "usuarios_app_genai"
    app_name: str = "Login Starter Kit"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    @property
    def cors_origins_list(self) -> list:
        """Convierte CORS_ORIGINS string a lista"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Instanciar configuración
settings = Settings()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CLIENTE SUPABASE
# ============================================================================

supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class SignUpRequest(BaseModel):
    """Modelo para registro de usuario"""
    email: EmailStr
    password: str


class SignInRequest(BaseModel):
    """Modelo para login de usuario"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Modelo de respuesta de usuario"""
    user_id: str
    email: str
    auth_source: str
    created_at: str
    

class AuthResponse(BaseModel):
    """Modelo de respuesta de autenticación"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Modelo de respuesta genérica"""
    message: str
    details: Optional[Dict[str, Any]] = None

# ============================================================================
# SEGURIDAD Y JWT
# ============================================================================

security = HTTPBearer()


def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Decodifica y valida el JWT de Supabase
    
    Args:
        token: JWT token de Supabase
        
    Returns:
        Payload decodificado del JWT
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency para validar JWT y obtener datos del usuario desde la tabla custom
    
    Args:
        credentials: Credenciales Bearer del header Authorization
        
    Returns:
        Diccionario con los datos del usuario desde USER_TABLE_NAME
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    token = credentials.credentials
    
    # Validar JWT
    payload = decode_jwt(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene user_id"
        )
    
    # Obtener datos del usuario desde la tabla custom
    try:
        response = supabase.table(settings.user_table_name).select("*").eq("user_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.error(f"Usuario {user_id} no encontrado en {settings.user_table_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado en la base de datos"
            )
        
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error al obtener usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos del usuario: {str(e)}"
        )

# ============================================================================
# LÓGICA DE NEGOCIO - PERSISTENCIA
# ============================================================================

async def ensure_user_persisted(user_id: str, email: str, auth_source: str) -> Dict[str, Any]:
    """
    Regla de Negocio A: Garantiza que el usuario existe en USER_TABLE_NAME
    Si no existe, lo crea con los datos esenciales.
    
    Args:
        user_id: UUID del usuario de Supabase
        email: Email del usuario
        auth_source: Fuente de autenticación ('email_password', 'google', 'outlook')
        
    Returns:
        Diccionario con los datos del usuario
    """
    try:
        # Verificar si el usuario ya existe
        response = supabase.table(settings.user_table_name).select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Usuario {user_id} ya existe en {settings.user_table_name}")
            return response.data[0]
        
        # Crear nuevo usuario
        logger.info(f"Creando nuevo usuario {user_id} en {settings.user_table_name}")
        new_user = {
            "user_id": user_id,
            "email": email,
            "auth_source": auth_source,
            "created_at": datetime.utcnow().isoformat()
        }
        
        insert_response = supabase.table(settings.user_table_name).insert(new_user).execute()
        
        if not insert_response.data or len(insert_response.data) == 0:
            raise Exception("No se pudo insertar el usuario")
        
        logger.info(f"Usuario {user_id} creado exitosamente")
        return insert_response.data[0]
        
    except Exception as e:
        logger.error(f"Error en ensure_user_persisted: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al persistir usuario: {str(e)}"
        )

# ============================================================================
# LIFESPAN Y APP INITIALIZATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para inicialización y limpieza"""
    # Startup
    logger.info(f"🚀 Iniciando {settings.app_name}")
    logger.info(f"📊 Tabla de usuarios: {settings.user_table_name}")
    logger.info(f"🌐 CORS Origins: {settings.cors_origins_list}")
    
    # Verificar tabla existe (opcional, para debugging)
    try:
        test = supabase.table(settings.user_table_name).select("user_id").limit(1).execute()
        logger.info(f"✅ Tabla {settings.user_table_name} verificada")
    except Exception as e:
        logger.warning(f"⚠️  No se pudo verificar la tabla {settings.user_table_name}: {str(e)}")
        logger.warning("Asegúrate de que la tabla existe en Supabase")
    
    yield
    
    # Shutdown
    logger.info(f"👋 Cerrando {settings.app_name}")


# ============================================================================
# APLICACIÓN FASTAPI
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    description="Servicio centralizado de autenticación con FastAPI y Supabase",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ENDPOINTS - FRONTEND
# ============================================================================

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Sirve el archivo index.html"""
    return FileResponse("index.html")

@app.get("/login.html", tags=["Frontend"])
async def serve_login():
    """Sirve el archivo login.html"""
    return FileResponse("login.html")

# ============================================================================
# ENDPOINTS - HEALTH CHECK
# ============================================================================

@app.get("/auth/health", response_model=MessageResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Verifica que el servicio está funcionando correctamente
    """
    # Verificar conexión con Supabase
    supabase_status = "✅ Conectado"
    try:
        test = supabase.table(settings.user_table_name).select("user_id").limit(1).execute()
    except Exception as e:
        supabase_status = f"❌ Error: {str(e)}"
    
    return MessageResponse(
        message=f"{settings.app_name} está funcionando correctamente",
        details={
            "app_name": settings.app_name,
            "user_table": settings.user_table_name,
            "supabase_status": supabase_status,
            "supabase_url": settings.supabase_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================================================
# ENDPOINTS - AUTENTICACIÓN EMAIL/PASSWORD
# ============================================================================

@app.post("/auth/signup", response_model=AuthResponse, tags=["Authentication"])
async def signup(signup_data: SignUpRequest):
    """
    Registro de nuevo usuario con email y password
    
    Flujo:
    1. Registra el usuario en Supabase Auth
    2. Persiste los datos en USER_TABLE_NAME (Regla A)
    3. Retorna JWT y datos del usuario
    """
    try:
        # Registrar en Supabase Auth
        logger.info(f"Registrando usuario: {signup_data.email}")
        auth_response = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear el usuario. Verifica que el email no esté registrado."
            )
        
        user_id = auth_response.user.id
        email = auth_response.user.email
        
        # Persistir en tabla custom (Regla A)
        user_data = await ensure_user_persisted(user_id, email, "email_password")
        
        # Obtener token
        access_token = auth_response.session.access_token if auth_response.session else None
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Usuario creado pero no se pudo obtener el token"
            )
        
        logger.info(f"Usuario {email} registrado exitosamente")
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["user_id"],
                email=user_data["email"],
                auth_source=user_data["auth_source"],
                created_at=user_data["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )


@app.post("/auth/signin", response_model=AuthResponse, tags=["Authentication"])
async def signin(signin_data: SignInRequest):
    """
    Login con email y password
    
    Flujo:
    1. Autentica con Supabase
    2. Valida JWT internamente
    3. Ejecuta persistencia (Regla A)
    4. Retorna JWT y datos del usuario
    """
    try:
        # Autenticar con Supabase
        logger.info(f"Autenticando usuario: {signin_data.email}")
        auth_response = supabase.auth.sign_in_with_password({
            "email": signin_data.email,
            "password": signin_data.password
        })
        
        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        user_id = auth_response.user.id
        email = auth_response.user.email
        access_token = auth_response.session.access_token
        
        # Validar JWT internamente
        decode_jwt(access_token)
        
        # Persistir en tabla custom (Regla A)
        user_data = await ensure_user_persisted(user_id, email, "email_password")
        
        logger.info(f"Usuario {email} autenticado exitosamente")
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["user_id"],
                email=user_data["email"],
                auth_source=user_data["auth_source"],
                created_at=user_data["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en signin: {str(e)}", exc_info=True)
        # Proporcionar más detalles del error para debugging
        error_detail = str(e)
        if "Invalid login credentials" in error_detail or "invalid_credentials" in error_detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )
        elif "Email not confirmed" in error_detail:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Por favor verifica tu email antes de iniciar sesión"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al autenticar: {error_detail}"
            )

# ============================================================================
# ENDPOINTS - OAUTH
# ============================================================================

@app.get("/auth/oauth/{provider_name}", tags=["OAuth"])
async def oauth_login(provider_name: str):
    """
    Inicia el flujo OAuth con el proveedor especificado
    
    Proveedores soportados: google, outlook (azure)
    
    Redirige a la página de autenticación del proveedor
    """
    try:
        # Mapeo de proveedores
        provider_map = {
            "google": "google",
            "outlook": "azure",
            "microsoft": "azure"
        }
        
        provider = provider_map.get(provider_name.lower())
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proveedor '{provider_name}' no soportado. Usa: google, outlook"
            )
        
        # Obtener URL de OAuth desde Supabase
        logger.info(f"🔐 Iniciando OAuth con proveedor: {provider}")
        
        # URL de callback - debe ser la URL completa de tu frontend
        redirect_to = f"http://localhost:{settings.port}/auth/callback"
        logger.info(f"📍 Redirect URL configurada: {redirect_to}")
        
        # Construir la URL de OAuth directamente
        # Formato: https://{project_ref}.supabase.co/auth/v1/authorize?provider={provider}&redirect_to={redirect_to}
        base_url = settings.supabase_url.replace('/rest/v1', '').replace('/v1', '')
        
        # Asegurarse de que la base_url no tenga trailing slash
        base_url = base_url.rstrip('/')
        
        # Construir URL de autorización OAuth
        oauth_url = f"{base_url}/auth/v1/authorize?provider={provider}&redirect_to={redirect_to}"
        
        logger.info(f"🌐 URL de OAuth construida: {oauth_url}")
        logger.info(f"🚀 Redirigiendo a Google OAuth...")
        
        # Redirigir directamente a la URL de OAuth de Supabase
        return RedirectResponse(url=oauth_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en oauth_login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar OAuth: {str(e)}"
        )


@app.get("/auth/callback", tags=["OAuth"])
async def oauth_callback(request: Request):
    """
    Callback de OAuth - Redirige al frontend
    
    Nota: Supabase envía los tokens en hash fragments (#access_token=...)
    que solo el cliente puede leer. El frontend debe capturar estos valores
    y llamar a /auth/oauth/complete para persistir el usuario.
    """
    # Redirigir al frontend - el hash fragment se mantendrá
    frontend_url = f"http://localhost:{settings.port}/"
    return RedirectResponse(url=frontend_url)


@app.post("/auth/oauth/complete", response_model=AuthResponse, tags=["OAuth"])
async def oauth_complete(request: Request):
    """
    Completa el flujo OAuth después de que el frontend captura el token
    
    Flujo:
    1. El frontend captura access_token del hash fragment
    2. Llama a este endpoint con el token
    3. Validamos el token y persistimos el usuario (Regla A)
    4. Retornamos los datos del usuario
    """
    try:
        # Obtener el token del header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización requerido"
            )
        
        access_token = auth_header.replace("Bearer ", "")
        
        # Validar y decodificar el token
        payload = decode_jwt(access_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido: falta user_id o email"
            )
        
        # Determinar el proveedor desde el token
        provider = payload.get("app_metadata", {}).get("provider", "unknown")
        auth_source = "google" if provider == "google" else "outlook" if provider == "azure" else provider
        
        logger.info(f"Completando OAuth para usuario {email} con proveedor {auth_source}")
        
        # Persistir usuario (Regla A)
        user_data = await ensure_user_persisted(user_id, email, auth_source)
        
        logger.info(f"Usuario {email} persistido exitosamente en {settings.user_table_name}")
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["user_id"],
                email=user_data["email"],
                auth_source=user_data["auth_source"],
                created_at=user_data["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en oauth_complete: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al completar OAuth: {str(e)}"
        )

# ============================================================================
# ENDPOINTS - PROTEGIDOS
# ============================================================================

@app.get("/api/v1/user/me", response_model=UserResponse, tags=["User"])
async def get_current_user_profile(current_user: Dict = Depends(get_current_user)):
    """
    Endpoint protegido que devuelve el perfil del usuario actual
    
    Requiere: Authorization: Bearer {token}
    """
    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        auth_source=current_user["auth_source"],
        created_at=current_user["created_at"]
    )

# ============================================================================
# MANEJO DE ERRORES GLOBAL
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler personalizado para HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para excepciones no manejadas"""
    logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor", "detail": str(exc)}
    )

# ============================================================================
# MAIN - PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando servidor en http://{settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )

