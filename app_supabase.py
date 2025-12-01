"""
BullAnalytics API with Supabase Integration
FastAPI backend for financial asset tracking with Supabase PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Query, Header, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, EmailStr
from cachetools import TTLCache
import uvicorn
import io
import base64
import json
import os
import re
import logging
import jwt
import requests
import feedparser
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv
from sib_api_v3_sdk import ApiClient, Configuration, TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException
from email_templates import (
    get_onboarding_email_template,
    get_alert_email_template,
    get_password_reset_email_template,
    get_subscription_confirmation_email_template
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pwumamzbicapuiqkwrey.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

if not SUPABASE_JWT_SECRET:
    raise ValueError("SUPABASE_JWT_SECRET environment variable is required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# User table name - using user_profiles (standard table)
USER_TABLE_NAME = "user_profiles"

# Brevo Email Configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# PayPal Configuration
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "live")  # 'sandbox' o 'live'
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "http://localhost:8080/subscription-success.html")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "http://localhost:8080/pricing.html")

# Initialize FastAPI app
app = FastAPI(
    title="BullAnalytics API",
    description="API for financial asset tracking powered by Yahoo Finance and Supabase",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Cache with 2-minute TTL (120 seconds)
cache = TTLCache(maxsize=200, ttl=120)

# Asset definitions
TRACKING_ASSETS = {
    "GOOGL": "Alphabet (Google)",
    "META": "Meta Platforms",
    "AMZN": "Amazon",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "AAPL": "Apple"
}

CRYPTO_ASSETS = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana",
    "ADA-USD": "Cardano",
    "XRP-USD": "Ripple",
    "DOGE-USD": "Dogecoin"
}

ARGENTINA_ASSETS = {
    "YPF": "YPF",
    "GGAL": "Grupo Financiero Galicia",
    "PAM": "Pampa Energia",
    "MELI": "MercadoLibre",
    "BMA": "Banco Macro",
    "SUPV": "Supervielle",
    "TEO": "Telecom Argentina",
    "LOMA": "Loma Negra"
}

PORTFOLIO_ASSETS = {
    "PFE": "Pfizer",
    "VIST": "Vista&Gas",
    "AMD": "AMD",
    "BABA": "Alibaba"
}

# ============================================
# AUTHENTICATION & AUTHORIZATION
# ============================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate JWT token from Supabase Auth and return user
    """
    try:
        token = credentials.credentials
        
        if not token:
            logger.warning("No token provided")
            raise HTTPException(status_code=401, detail="No authentication token provided")
        
        # Verify token with Supabase
        try:
            user_response = supabase.auth.get_user(token)
        except Exception as auth_error:
            logger.error(f"Error validating token with Supabase: {str(auth_error)}")
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(auth_error)}")
        
        if not user_response or not user_response.user:
            logger.warning("Token validation returned no user")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        logger.info(f"User authenticated: {user_response.user.id}")
        return user_response.user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ============================================
# PYDANTIC MODELS
# ============================================

class AssetData(BaseModel):
    name: str
    ticker: str
    price: float
    pe_ratio: Optional[float]
    all_time_high: float
    diff_from_max: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    cash_flow: Optional[float] = None
    dividend_yield: Optional[float] = None
    year_low: Optional[float] = None
    year_high: Optional[float] = None
    avg_volume: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    revenue_quarterly_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    price_to_book: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    enterprise_value: Optional[float] = None
    enterprise_to_revenue: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    total_assets: Optional[float] = None
    book_value: Optional[float] = None
    beta: Optional[float] = None
    logo_url: Optional[str] = None

class RuleCreate(BaseModel):
    name: str
    rule_type: str  # 'price_below', 'price_above', 'pe_below', 'pe_above', 'max_distance'
    ticker: str
    value: float
    email: str

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    value: Optional[float] = None

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WatchlistAssetAdd(BaseModel):
    ticker: str
    asset_name: str

class CouponValidate(BaseModel):
    code: str
    plan_name: str

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_asset_data(ticker: str, name: str) -> Optional[AssetData]:
    """
    Fetch asset data from Yahoo Finance with caching.
    """
    cache_window = int(datetime.now().timestamp() // 120)
    cache_key = f"{ticker}_{cache_window}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="max")
        
        logo_url = None
        if 'logo_url' in info and info.get('logo_url'):
            logo_url = info.get('logo_url')
        
        if hist.empty:
            return None
        
        all_time_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        diff_from_max = (current_price - all_time_high) / all_time_high
        pe_ratio = info.get('trailingPE')
        
        hist_1y = stock.history(period="1y")
        year_high = float(hist_1y['High'].max()) if not hist_1y.empty else None
        year_low = float(hist_1y['Low'].min()) if not hist_1y.empty else None
        
        volume = float(hist['Volume'].iloc[-1]) if not hist.empty else None
        market_cap = info.get('marketCap')
        cash_flow = info.get('operatingCashflow') or info.get('freeCashflow')
        dividend_yield = info.get('dividendYield')
        avg_volume = info.get('averageVolume')
        
        # Calculate RSI (14 period)
        rsi = None
        if len(hist) >= 14:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = float(100 - (100 / (1 + rs.iloc[-1]))) if not rs.empty and not rs.isna().iloc[-1] else None
        
        # SMA 50 and 200
        sma_50 = float(hist['Close'].tail(50).mean()) if len(hist) >= 50 else None
        sma_200 = float(hist['Close'].tail(200).mean()) if len(hist) >= 200 else None
        
        # MACD
        macd = None
        if len(hist) >= 26:
            ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = float((ema_12 - ema_26).iloc[-1]) if not (ema_12 - ema_26).empty else None
        
        asset_data = AssetData(
            name=f"{name} ({ticker})",
            ticker=ticker,
            price=float(current_price),
            pe_ratio=float(pe_ratio) if pe_ratio else None,
            all_time_high=float(all_time_high),
            diff_from_max=float(diff_from_max),
            volume=volume,
            market_cap=float(market_cap) if market_cap else None,
            cash_flow=float(cash_flow) if cash_flow else None,
            dividend_yield=float(dividend_yield) if dividend_yield else None,
            year_low=year_low,
            year_high=year_high,
            avg_volume=float(avg_volume) if avg_volume else None,
            rsi=rsi,
            macd=macd,
            sma_50=sma_50,
            sma_200=sma_200,
            revenue=float(info.get('totalRevenue')) if info.get('totalRevenue') else None,
            profit_margin=float(info.get('profitMargins')) if info.get('profitMargins') else None,
            return_on_equity=float(info.get('returnOnEquity')) if info.get('returnOnEquity') else None,
            debt_to_equity=float(info.get('debtToEquity')) if info.get('debtToEquity') else None,
            beta=float(info.get('beta')) if info.get('beta') else None,
            logo_url=logo_url
        )
        
        cache[cache_key] = asset_data
        return asset_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# ============================================
# AUTHENTICATION HELPERS
# ============================================

def decode_jwt(token: str) -> Dict[str, Any]:
    """Decodifica y valida el JWT de Supabase"""
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
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

async def ensure_user_persisted(user_id: str, email: str, auth_source: str) -> Dict[str, Any]:
    """Garantiza que el usuario existe en user_profiles"""
    try:
        # Verificar si el usuario ya existe (user_profiles usa 'id' como PK)
        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Usuario {user_id} ya existe en {USER_TABLE_NAME}")
            user_data = response.data[0]
            # Agregar auth_source al response para compatibilidad
            user_data["auth_source"] = auth_source
            return user_data
        
        # Crear nuevo usuario en user_profiles
        logger.info(f"Creando nuevo usuario {user_id} en {USER_TABLE_NAME}")
        new_user = {
            "id": user_id,
            "email": email,
            "full_name": None,
            "avatar_url": None,
            "preferences": {},
            "onboarding_completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        insert_response = supabase.table(USER_TABLE_NAME).insert(new_user).execute()
        
        if not insert_response.data or len(insert_response.data) == 0:
            raise Exception("No se pudo insertar el usuario")
        
        logger.info(f"Usuario {user_id} creado exitosamente")
        user_data = insert_response.data[0]
        # Agregar auth_source al response para compatibilidad
        user_data["auth_source"] = auth_source
        
        # Crear suscripción automática con trial de 14 días
        await create_default_subscription(user_id)
        
        # Enviar email de bienvenida/onboarding
        try:
            user_name = user_data.get("full_name") or email.split("@")[0]
            email_template = get_onboarding_email_template(user_name, email)
            send_result = send_alert_email(
                to_email=email,
                subject=email_template["subject"],
                html_content=email_template["html_content"]
            )
            if send_result.get("success"):
                logger.info(f"✅ Email de bienvenida enviado a {email}")
            else:
                logger.warning(f"⚠️ No se pudo enviar email de bienvenida: {send_result.get('error')}")
        except Exception as email_error:
            logger.error(f"Error enviando email de bienvenida: {str(email_error)}")
            # No fallar el registro si el email falla
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error en ensure_user_persisted: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al persistir usuario: {str(e)}"
        )

async def create_default_subscription(user_id: str):
    """Crea una suscripción por defecto con plan free y trial de 7 días"""
    try:
        # Obtener el plan "free" (plan gratuito con trial)
        plan_response = supabase.table("subscription_plans").select("*").eq("name", "free").execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            logger.error("Plan 'free' no encontrado")
            return
        
        plan = plan_response.data[0]
        plan_id = plan["id"]
        
        # Calcular fechas de trial (7 días desde ahora)
        now = datetime.utcnow()
        trial_end = now + timedelta(days=7)
        
        # Crear suscripción con trial
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": trial_end.isoformat()
        }
        
        subscription_response = supabase.table("subscriptions").insert(subscription_data).execute()
        
        if subscription_response.data:
            logger.info(f"Suscripción con trial creada para usuario {user_id}")
        else:
            logger.error(f"Error al crear suscripción para usuario {user_id}")
            
    except Exception as e:
        logger.error(f"Error creando suscripción por defecto: {str(e)}")
        # No lanzar excepción para no interrumpir el registro del usuario

# ============================================
# AUTHENTICATION MODELS
# ============================================

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    auth_source: str
    created_at: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============================================
# ASSET ENDPOINTS (Unchanged)
# ============================================

@app.get("/")
async def root():
    """Serve the landing page"""
    return FileResponse("index.html")

@app.get("/api/tracking-assets", response_model=List[AssetData])
async def get_tracking_assets():
    """Get tracking assets data"""
    results = []
    for ticker, name in TRACKING_ASSETS.items():
        asset_data = get_asset_data(ticker, name)
        if asset_data:
            results.append(asset_data)
    
    if not results:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los datos")
    
    return results

@app.get("/api/portfolio-assets", response_model=List[AssetData])
async def get_portfolio_assets():
    """Get portfolio assets data"""
    results = []
    for ticker, name in PORTFOLIO_ASSETS.items():
        asset_data = get_asset_data(ticker, name)
        if asset_data:
            results.append(asset_data)
    
    if not results:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los datos")
    
    return results

@app.get("/api/crypto-assets", response_model=List[AssetData])
async def get_crypto_assets():
    """Get crypto assets data"""
    results = []
    for ticker, name in CRYPTO_ASSETS.items():
        asset_data = get_asset_data(ticker, name)
        if asset_data:
            results.append(asset_data)
    
    if not results:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los datos")
    
    return results

@app.get("/api/argentina-assets", response_model=List[AssetData])
async def get_argentina_assets():
    """Get Argentina assets data"""
    results = []
    for ticker, name in ARGENTINA_ASSETS.items():
        asset_data = get_asset_data(ticker, name)
        if asset_data:
            results.append(asset_data)
    
    if not results:
        raise HTTPException(status_code=500, detail="No se pudieron cargar los datos")
    
    return results

# ============================================
# NEWS ENDPOINT
# ============================================

@app.get("/api/news")
async def get_news(category: str = Query("general", description="News category")):
    """Get financial news from Yahoo Finance RSS with category support"""
    
    # Map categories to RSS URLs
    rss_urls = {
        "general": "https://finance.yahoo.com/news/rssindex",
        "crypto": "https://finance.yahoo.com/topic/crypto/rss",
        "tech": "https://finance.yahoo.com/topic/tech/rss",
        "usa": "https://finance.yahoo.com/topic/stock-market-news/rss",
        "china": "https://finance.yahoo.com/topic/china/rss",  # Best effort
        "europe": "https://finance.yahoo.com/topic/europe/rss",  # Best effort
        "ai": "https://finance.yahoo.com/topic/tech/rss"  # Fallback to tech for AI if no specific feed
    }
    
    feed_url = rss_urls.get(category.lower(), rss_urls["general"])
    
    # Cache key includes category
    cache_key = f"news_{category}_{int(datetime.now().timestamp() // 1800)}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        feed = feedparser.parse(feed_url)
        
        # If feed is empty or error, fallback to general
        if not feed.entries and category != "general":
            feed = feedparser.parse(rss_urls["general"])
        
        news_items = []
        for entry in feed.entries[:20]:
            # Try to find image
            image_url = None
            if 'media_content' in entry:
                image_url = entry.media_content[0]['url']
            elif 'media_thumbnail' in entry:
                image_url = entry.media_thumbnail[0]['url']
            
            # Clean summary (remove HTML tags if any)
            summary = entry.get('summary', '')
            summary = re.sub('<[^<]+?>', '', summary)
            
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get('published', ''),
                "summary": summary[:200] + '...' if len(summary) > 200 else summary,
                "image": image_url,
                "source": entry.get('source', {}).get('title', 'Yahoo Finance')
            })
        
        cache[cache_key] = news_items
        return news_items
    except Exception as e:
        logger.error(f"Error fetching news: {e}", exc_info=True)
        return []

# ============================================
# RULES ENDPOINTS (Supabase Integration)
# ============================================

@app.get("/api/rules")
async def get_rules(user = Depends(get_current_user)):
    """Get all rules for authenticated user"""
    try:
        logger.info(f"Fetching rules for user {user.id}")
        response = supabase.table("rules") \
            .select("*") \
            .eq("user_id", user.id) \
            .order("created_at", desc=True) \
            .execute()
        
        # Asegurar que siempre devolvemos un array, incluso si response.data es None
        rules = response.data if response.data is not None else []
        
        if len(rules) == 0:
            logger.info(f"No rules found for user {user.id}")
        else:
            logger.info(f"Found {len(rules)} rules for user {user.id}")
        
        return rules
    except Exception as e:
        logger.error(f"Error fetching rules for user {user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

@app.post("/api/rules")
async def create_rule(rule: RuleCreate, user = Depends(get_current_user)):
    """Create a new rule"""
    try:
        logger.info(f"Creating rule for user {user.id}: {rule.name} ({rule.rule_type})")
        
        # Check user's plan limits
        try:
            check_result = supabase.rpc("check_user_plan_limit", {
                "p_user_id": user.id,
                "p_limit_type": "max_rules"
            }).execute()
            
            # La función RPC devuelve un booleano directamente
            # Si devuelve False o None, el usuario no puede crear más reglas
            can_create = check_result.data if check_result.data is not None else True
            
            if not can_create:
                raise HTTPException(
                    status_code=403,
                    detail="Has alcanzado el límite de reglas de tu plan. Actualiza tu suscripción."
                )
        except HTTPException:
            raise
        except Exception as rpc_error:
            logger.warning(f"Error checking plan limit, continuando: {str(rpc_error)}")
            # Continuar si hay error en la verificación del límite (no bloquear creación)
        
        rule_data = {
            "user_id": user.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "ticker": rule.ticker,
            "value_threshold": rule.value,
            "email": rule.email,
            "is_active": True
        }
        
        logger.info(f"Inserting rule data: {rule_data}")
        response = supabase.table("rules").insert(rule_data).execute()
        
        if not response.data or len(response.data) == 0:
            logger.error("No data returned from Supabase insert")
            raise HTTPException(status_code=500, detail="No se pudo crear la regla. No se recibieron datos de respuesta.")
        
        logger.info(f"Rule created successfully: {response.data[0].get('id')}")
        return {
            "message": "Rule created successfully",
            "rule": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rule: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")

@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, rule: RuleUpdate, user = Depends(get_current_user)):
    """Update an existing rule"""
    try:
        # Build update data
        update_data = {}
        if rule.name is not None:
            update_data["name"] = rule.name
        if rule.is_active is not None:
            update_data["is_active"] = rule.is_active
        if rule.value is not None:
            update_data["value_threshold"] = rule.value
        
        response = supabase.table("rules") \
            .update(update_data) \
            .eq("id", rule_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return {
            "message": "Rule updated successfully",
            "rule": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rule: {str(e)}")

@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: str, user = Depends(get_current_user)):
    """Delete a rule"""
    try:
        response = supabase.table("rules") \
            .delete() \
            .eq("id", rule_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return {"message": "Rule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting rule: {str(e)}")

# ============================================
# WATCHLISTS ENDPOINTS (Supabase  Integration)
# ============================================

@app.get("/api/watchlists")
async def get_watchlists(user = Depends(get_current_user)):
    """Get all watchlists for authenticated user"""
    try:
        response = supabase.table("watchlists") \
            .select("*, watchlist_assets(*)") \
            .eq("user_id", user.id) \
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching watchlists: {str(e)}")

@app.post("/api/watchlists")
async def create_watchlist(watchlist: WatchlistCreate, user = Depends(get_current_user)):
    """Create a new watchlist"""
    try:
        watchlist_data = {
            "user_id": user.id,
            "name": watchlist.name,
            "description": watchlist.description
        }
        
        response = supabase.table("watchlists").insert(watchlist_data).execute()
        
        return {
            "message": "Watchlist created successfully",
            "watchlist": response.data[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating watchlist: {str(e)}")

@app.post("/api/watchlists/{watchlist_id}/assets")
async def add_asset_to_watchlist(
    watchlist_id: str,
    asset: WatchlistAssetAdd,
    user = Depends(get_current_user)
):
    """Add an asset to a watchlist"""
    try:
        # Verify watchlist belongs to user
        watchlist_response = supabase.table("watchlists") \
            .select("id") \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        asset_data = {
            "watchlist_id": watchlist_id,
            "ticker": asset.ticker,
            "asset_name": asset.asset_name
        }
        
        response = supabase.table("watchlist_assets").insert(asset_data).execute()
        
        return {
            "message": "Asset added to watchlist",
            "asset": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding asset: {str(e)}")

@app.delete("/api/watchlists/{watchlist_id}")
async def delete_watchlist(watchlist_id: str, user = Depends(get_current_user)):
    """Delete a watchlist"""
    try:
        response = supabase.table("watchlists") \
            .delete() \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        return {"message": "Watchlist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting watchlist: {str(e)}")

# ============================================
# ALERTS ENDPOINTS (Supabase Integration)
# ============================================

@app.get("/api/alerts")
async def get_alerts(user = Depends(get_current_user)):
    """Get all alerts for authenticated user"""
    try:
        response = supabase.table("alerts") \
            .select("*") \
            .eq("user_id", user.id) \
            .order("created_at", desc=True) \
            .limit(100) \
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@app.patch("/api/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, user = Depends(get_current_user)):
    """Mark an alert as read"""
    try:
        response = supabase.table("alerts") \
            .update({"is_read": True, "read_at": datetime.now().isoformat()}) \
            .eq("id", alert_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating alert: {str(e)}")

# ============================================
# AUTHENTICATION HELPERS
# ============================================

def decode_jwt(token: str) -> Dict[str, Any]:
    """Decodifica y valida el JWT de Supabase"""
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
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

async def ensure_user_persisted(user_id: str, email: str, auth_source: str) -> Dict[str, Any]:
    """Garantiza que el usuario existe en user_profiles"""
    try:
        # Verificar si el usuario ya existe (user_profiles usa 'id' como PK)
        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Usuario {user_id} ya existe en {USER_TABLE_NAME}")
            user_data = response.data[0]
            # Agregar auth_source al response para compatibilidad
            user_data["auth_source"] = auth_source
            return user_data
        
        # Crear nuevo usuario en user_profiles
        logger.info(f"Creando nuevo usuario {user_id} en {USER_TABLE_NAME}")
        new_user = {
            "id": user_id,
            "email": email,
            "full_name": None,
            "avatar_url": None,
            "preferences": {},
            "onboarding_completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        insert_response = supabase.table(USER_TABLE_NAME).insert(new_user).execute()
        
        if not insert_response.data or len(insert_response.data) == 0:
            raise Exception("No se pudo insertar el usuario")
        
        logger.info(f"Usuario {user_id} creado exitosamente")
        user_data = insert_response.data[0]
        # Agregar auth_source al response para compatibilidad
        user_data["auth_source"] = auth_source
        
        # Crear suscripción automática con trial de 14 días
        await create_default_subscription(user_id)
        
        # Enviar email de bienvenida/onboarding
        try:
            user_name = user_data.get("full_name") or email.split("@")[0]
            email_template = get_onboarding_email_template(user_name, email)
            send_result = send_alert_email(
                to_email=email,
                subject=email_template["subject"],
                html_content=email_template["html_content"]
            )
            if send_result.get("success"):
                logger.info(f"✅ Email de bienvenida enviado a {email}")
            else:
                logger.warning(f"⚠️ No se pudo enviar email de bienvenida: {send_result.get('error')}")
        except Exception as email_error:
            logger.error(f"Error enviando email de bienvenida: {str(email_error)}")
            # No fallar el registro si el email falla
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error en ensure_user_persisted: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al persistir usuario: {str(e)}"
        )

async def create_default_subscription(user_id: str):
    """Crea una suscripción por defecto con plan free y trial de 7 días"""
    try:
        # Obtener el plan "free" (plan gratuito con trial)
        plan_response = supabase.table("subscription_plans").select("*").eq("name", "free").execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            logger.error("Plan 'free' no encontrado")
            return
        
        plan = plan_response.data[0]
        plan_id = plan["id"]
        
        # Calcular fechas de trial (7 días desde ahora)
        now = datetime.utcnow()
        trial_end = now + timedelta(days=7)
        
        # Crear suscripción con trial
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "trial_start": now.isoformat(),
            "trial_end": trial_end.isoformat(),
            "current_period_start": now.isoformat(),
            "current_period_end": trial_end.isoformat()
        }
        
        subscription_response = supabase.table("subscriptions").insert(subscription_data).execute()
        
        if subscription_response.data:
            logger.info(f"Suscripción con trial creada para usuario {user_id}")
        else:
            logger.error(f"Error al crear suscripción para usuario {user_id}")
            
    except Exception as e:
        logger.error(f"Error creando suscripción por defecto: {str(e)}")
        # No lanzar excepción para no interrumpir el registro del usuario

# ============================================
# AUTHENTICATION MODELS
# ============================================

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    auth_source: str
    created_at: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.post("/auth/signup", response_model=AuthResponse, tags=["Authentication"])
async def signup(signup_data: SignUpRequest):
    """Registro de nuevo usuario con email y password"""
    try:
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
        
        # Persistir en tabla custom
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
                user_id=user_data["id"],  # user_profiles usa 'id' como PK
                email=user_data["email"],
                auth_source=user_data.get("auth_source", auth_source),
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
    """Login con email y password"""
    try:
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
        
        # Persistir en tabla custom
        user_data = await ensure_user_persisted(user_id, email, "email_password")
        
        logger.info(f"Usuario {email} autenticado exitosamente")
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["id"],  # user_profiles usa 'id' como PK
                email=user_data["email"],
                auth_source=user_data.get("auth_source", auth_source),
                created_at=user_data["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en signin: {str(e)}", exc_info=True)
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

@app.get("/auth/oauth/{provider_name}", tags=["OAuth"])
async def oauth_login(provider_name: str):
    """Inicia el flujo OAuth con el proveedor especificado"""
    try:
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
        
        logger.info(f"🔐 Iniciando OAuth con proveedor: {provider}")
        
        # URL de callback - debe ser la URL completa de tu frontend (puerto 8080)
        redirect_to = "http://localhost:8080/login.html"
        logger.info(f"📍 Redirect URL configurada: {redirect_to}")
        
        # Construir la URL de OAuth directamente
        base_url = SUPABASE_URL.replace('/rest/v1', '').replace('/v1', '').rstrip('/')
        
        # Construir URL de autorización OAuth
        oauth_url = f"{base_url}/auth/v1/authorize?provider={provider}&redirect_to={redirect_to}"
        
        logger.info(f"🌐 URL de OAuth construida: {oauth_url}")
        logger.info(f"🚀 Redirigiendo a {provider} OAuth...")
        
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
    """Callback de OAuth - Redirige al frontend"""
    # Redirigir al frontend - el hash fragment se mantendrá
    frontend_url = "http://localhost:8080/login.html"
    return RedirectResponse(url=frontend_url)

@app.post("/auth/oauth/complete", response_model=AuthResponse, tags=["OAuth"])
async def oauth_complete(request: Request):
    """Completa el flujo OAuth después de que el frontend captura el token"""
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
        
        # Persistir usuario
        user_data = await ensure_user_persisted(user_id, email, auth_source)
        
        logger.info(f"Usuario {email} persistido exitosamente en {USER_TABLE_NAME}")
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["id"],  # user_profiles usa 'id' como PK
                email=user_data["email"],
                auth_source=user_data.get("auth_source", auth_source),
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

@app.get("/api/v1/user/me", response_model=UserResponse, tags=["User"])
async def get_current_user_profile(user = Depends(get_current_user)):
    """Endpoint protegido que devuelve el perfil del usuario actual"""
    try:
        # user es un objeto de Supabase Auth con id
        user_id = user.id
        
        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado en la base de datos"
            )
        
        user_data = response.data[0]
        # user_profiles no tiene auth_source, usar valor por defecto
        auth_source = user_data.get("auth_source", "email_password")
        
        return UserResponse(
            user_id=user_data["id"],  # user_profiles usa 'id' como PK
            email=user_data["email"],
            auth_source=auth_source,
            created_at=user_data["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos del usuario: {str(e)}"
        )

# ============================================
# SUBSCRIPTIONS ENDPOINTS
# ============================================

@app.get("/api/subscriptions/current")
async def get_current_subscription(user = Depends(get_current_user)):
    """Obtiene la suscripción actual del usuario"""
    try:
        response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = response.data[0]
        plan = subscription.get("subscription_plans", {})
        
        return {
            "id": subscription["id"],
            "user_id": subscription["user_id"],
            "plan_id": subscription["plan_id"],
            "plan_name": plan.get("name", "free"),
            "display_name": plan.get("display_name", "Plan Básico"),
            "price": str(plan.get("price", "0.00")),
            "status": subscription["status"],
            "trial_start": subscription.get("trial_start"),
            "trial_end": subscription.get("trial_end"),
            "current_period_start": subscription.get("current_period_start"),
            "current_period_end": subscription.get("current_period_end"),
            "created_at": subscription.get("created_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscription: {str(e)}")

# ============================================
# SUBSCRIPTIONS ENDPOINTS
# ============================================

@app.get("/api/subscription-plans")
async def get_subscription_plans():
    """Obtiene todos los planes de suscripción disponibles"""
    try:
        response = supabase.table("subscription_plans") \
            .select("*") \
            .eq("is_active", True) \
            .order("sort_order", desc=False) \
            .execute()
        
        if not response.data:
            return []
        
        return response.data
    except Exception as e:
        logger.error(f"Error fetching subscription plans: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching subscription plans: {str(e)}")

@app.get("/api/subscriptions/current")
async def get_current_subscription(user = Depends(get_current_user)):
    """Obtiene la suscripción actual del usuario"""
    try:
        response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        subscription = response.data[0]
        plan = subscription.get("subscription_plans", {})
        
        return {
            "id": subscription["id"],
            "user_id": subscription["user_id"],
            "plan_id": subscription["plan_id"],
            "plan_name": plan.get("name", "free"),
            "display_name": plan.get("display_name", "Plan Básico"),
            "price": str(plan.get("price", "0.00")),
            "status": subscription["status"],
            "trial_start": subscription.get("trial_start"),
            "trial_end": subscription.get("trial_end"),
            "current_period_start": subscription.get("current_period_start"),
            "current_period_end": subscription.get("current_period_end"),
            "created_at": subscription.get("created_at")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscription: {str(e)}")

# ============================================
# COUPONS ENDPOINTS (Supabase Integration)
# ============================================

@app.post("/api/coupons/validate")
async def validate_coupon(coupon: CouponValidate, user = Depends(get_current_user)):
    """Validate a coupon code"""
    try:
        # Get plan_id
        plan_response = supabase.table("subscription_plans") \
            .select("id") \
            .eq("name", coupon.plan_name) \
            .single() \
            .execute()
        
        if not plan_response.data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Validate coupon using Supabase function
        validation_response = supabase.rpc("validate_coupon", {
            "p_code": coupon.code,
            "p_user_id": user.id,
            "p_plan_id": plan_response.data["id"]
        }).execute()
        
        return validation_response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating coupon: {str(e)}")

# ============================================
# STATIC FILES & HTML PAGES
# ============================================

# Mount static files
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/images", StaticFiles(directory="images"), name="images")

# Serve HTML files
@app.get("/dashboard.html")
async def dashboard():
    return FileResponse("dashboard.html")

@app.get("/news.html")
async def news():
    return FileResponse("news.html")

@app.get("/pricing.html")
async def pricing():
    return FileResponse("pricing.html")

@app.get("/rules.html")
async def rules():
    return FileResponse("rules.html")

@app.get("/account.html")
async def account():
    return FileResponse("account.html")

@app.get("/login.html")
async def login():
    return FileResponse("login.html")

@app.get("/subscription-success.html")
async def subscription_success():
    return FileResponse("subscription-success.html")

@app.get("/")
async def root():
    """Serve the landing page"""
    return FileResponse("index.html")

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        supabase.table("subscription_plans").select("count").execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================
# EMAIL FUNCTIONS (Brevo Integration)
# ============================================

def send_alert_email(to_email: str, subject: str, html_content: str, sender_name: str = "BullAnalytics", sender_email: str = "noreply@aperturaia.com"):
    """Envía un correo de alerta usando Brevo"""
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY no configurada en variables de entorno")
        return {"success": False, "error": "BREVO_API_KEY no configurada"}
    
    try:
        configuration = Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        
        api_instance = TransactionalEmailsApi(ApiClient(configuration))
        
        send_smtp_email = {
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'to': [{'email': to_email}],
            'subject': subject,
            'htmlContent': html_content
        }
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"✅ Email enviado exitosamente a {to_email}: {api_response.message_id}")
        return {
            "success": True,
            "message_id": api_response.message_id,
            "to": to_email
        }
        
    except ApiException as e:
        error_msg = f"Error enviando email: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": str(e),
            "status_code": e.status if hasattr(e, 'status') else None
        }
    except Exception as e:
        error_msg = f"Error inesperado enviando email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/email/test")
async def test_email(email: str = Query(..., description="Email destino para prueba")):
    """Endpoint de prueba para enviar un email usando Brevo"""
    if not BREVO_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="BREVO_API_KEY no configurada. Por favor, configura la variable de entorno."
        )
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 BullAnalytics</h1>
            <p>Prueba de Email Exitosa</p>
        </div>
        <div class="content">
            <h2>¡Hola! 👋</h2>
            <p>Este es un correo de prueba desde <strong>BullAnalytics</strong> usando <strong>Brevo</strong>.</p>
            <p>Si recibiste este correo, significa que la integración con Brevo está funcionando correctamente.</p>
            <p><strong>Detalles de la prueba:</strong></p>
            <ul>
                <li>✅ Servicio: Brevo (Sendinblue)</li>
                <li>✅ Fecha: {timestamp}</li>
                <li>✅ Estado: Enviado exitosamente</li>
            </ul>
            <p>Ahora puedes configurar alertas financieras que se enviarán automáticamente cuando se cumplan tus reglas.</p>
            <a href="http://localhost:8080/rules.html" class="button">Gestionar Alertas</a>
        </div>
        <div class="footer">
            <p>Este es un correo automático de BullAnalytics.</p>
            <p>No respondas a este correo.</p>
        </div>
    </body>
    </html>
    """
    
    result = send_alert_email(
        to_email=email,
        subject="✅ Prueba de Email - BullAnalytics",
        html_content=html_content
    )
    
    if result.get("success"):
        return {
            "message": "Email enviado exitosamente",
            "message_id": result.get("message_id"),
            "to": email
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Error enviando email: {result.get('error', 'Error desconocido')}"
        )

@app.post("/api/email/test-templates")
async def test_all_templates(email: str = Query(..., description="Email destino para probar todos los templates")):
    """Endpoint de prueba para enviar todos los templates de email"""
    if not BREVO_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="BREVO_API_KEY no configurada. Por favor, configura la variable de entorno."
        )
    
    results = []
    
    # 1. Template de Onboarding
    try:
        user_name = email.split("@")[0]
        onboarding_template = get_onboarding_email_template(user_name, email)
        result = send_alert_email(
            to_email=email,
            subject=onboarding_template["subject"],
            html_content=onboarding_template["html_content"]
        )
        results.append({
            "template": "onboarding",
            "success": result.get("success", False),
            "message_id": result.get("message_id") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        })
    except Exception as e:
        results.append({
            "template": "onboarding",
            "success": False,
            "error": str(e)
        })
    
    # 2. Template de Alerta Financiera (price_below)
    try:
        alert_template = get_alert_email_template(
            rule_name="Alerta de Prueba - NVDA",
            ticker="NVDA",
            alert_message="NVDA está por debajo de $500",
            current_price=495.50,
            threshold=500.00,
            rule_type="price_below"
        )
        result = send_alert_email(
            to_email=email,
            subject=alert_template["subject"],
            html_content=alert_template["html_content"]
        )
        results.append({
            "template": "alert_price_below",
            "success": result.get("success", False),
            "message_id": result.get("message_id") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        })
    except Exception as e:
        results.append({
            "template": "alert_price_below",
            "success": False,
            "error": str(e)
        })
    
    # 3. Template de Alerta Financiera (price_above)
    try:
        alert_template = get_alert_email_template(
            rule_name="Alerta de Prueba - AAPL",
            ticker="AAPL",
            alert_message="AAPL está por encima de $180",
            current_price=185.75,
            threshold=180.00,
            rule_type="price_above"
        )
        result = send_alert_email(
            to_email=email,
            subject=alert_template["subject"],
            html_content=alert_template["html_content"]
        )
        results.append({
            "template": "alert_price_above",
            "success": result.get("success", False),
            "message_id": result.get("message_id") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        })
    except Exception as e:
        results.append({
            "template": "alert_price_above",
            "success": False,
            "error": str(e)
        })
    
    # 4. Template de Reset de Contraseña
    try:
        reset_template = get_password_reset_email_template(
            reset_link="https://bullanalytics.com/reset?token=test_token_12345",
            user_name=user_name
        )
        result = send_alert_email(
            to_email=email,
            subject=reset_template["subject"],
            html_content=reset_template["html_content"]
        )
        results.append({
            "template": "password_reset",
            "success": result.get("success", False),
            "message_id": result.get("message_id") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        })
    except Exception as e:
        results.append({
            "template": "password_reset",
            "success": False,
            "error": str(e)
        })
    
    # 5. Template de Confirmación de Suscripción
    try:
        subscription_template = get_subscription_confirmation_email_template(
            plan_name="Plus",
            price=29.99,
            billing_period="mensual"
        )
        result = send_alert_email(
            to_email=email,
            subject=subscription_template["subject"],
            html_content=subscription_template["html_content"]
        )
        results.append({
            "template": "subscription_confirmation",
            "success": result.get("success", False),
            "message_id": result.get("message_id") if result.get("success") else None,
            "error": result.get("error") if not result.get("success") else None
        })
    except Exception as e:
        results.append({
            "template": "subscription_confirmation",
            "success": False,
            "error": str(e)
        })
    
    # Resumen
    successful = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    return {
        "message": f"Prueba de templates completada: {successful}/{total} enviados exitosamente",
        "to": email,
        "results": results,
        "summary": {
            "total": total,
            "successful": successful,
            "failed": total - successful
        }
    }

# ============================================
# PAYPAL SUBSCRIPTION ENDPOINTS
# ============================================

class CreateSubscriptionRequest(BaseModel):
    plan_name: str  # 'plus' o 'pro'

def get_paypal_access_token() -> str:
    """Obtiene token de acceso de PayPal"""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="PayPal credentials no configuradas. Configura PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET en .env"
        )
    
    auth = base64.b64encode(
        f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            headers=headers,
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Error obteniendo token de PayPal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error conectando con PayPal: {str(e)}"
        )

@app.post("/api/subscriptions/create")
async def create_subscription(
    request: CreateSubscriptionRequest,
    user = Depends(get_current_user)
):
    """
    Crea una nueva suscripción en PayPal y guarda referencia en Supabase
    """
    try:
        logger.info(f"Creando suscripción para usuario {user.id}, plan: {request.plan_name}")
        
        # 1. Obtener plan de Supabase
        plan_response = supabase.table("subscription_plans") \
            .select("*") \
            .eq("name", request.plan_name) \
            .execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            raise HTTPException(status_code=404, detail=f"Plan '{request.plan_name}' no encontrado")
        
        plan = plan_response.data[0]
        paypal_plan_id = plan.get("paypal_plan_id")
        
        if not paypal_plan_id:
            raise HTTPException(
                status_code=400,
                detail=f"Plan '{request.plan_name}' no tiene paypal_plan_id configurado. Configúralo en Supabase."
            )
        
        # 2. Verificar si el usuario ya tiene una suscripción activa
        existing_sub = supabase.table("subscriptions") \
            .select("*") \
            .eq("user_id", user.id) \
            .in_("status", ["active", "pending_approval"]) \
            .execute()
        
        if existing_sub.data and len(existing_sub.data) > 0:
            raise HTTPException(
                status_code=400,
                detail="Ya tienes una suscripción activa o pendiente. Cancela la actual antes de crear una nueva."
            )
        
        # 3. Obtener email del usuario
        user_profile = supabase.table("user_profiles") \
            .select("email") \
            .eq("id", user.id) \
            .single() \
            .execute()
        
        user_email = user_profile.data.get("email") if user_profile.data else user.id
        
        # 4. Crear suscripción en PayPal
        access_token = get_paypal_access_token()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        payload = {
            "plan_id": paypal_plan_id,
            "start_time": None,  # Inicia inmediatamente tras aprobación
            "subscriber": {
                "email_address": user_email,
            },
            "application_context": {
                "brand_name": "BullAnalytics",
                "locale": "es-ES",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "return_url": PAYPAL_RETURN_URL,
                "cancel_url": PAYPAL_CANCEL_URL
            }
        }
        
        logger.info(f"Creando suscripción en PayPal con plan_id: {paypal_plan_id}")
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/billing/subscriptions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 201:
            error_detail = response.json() if response.content else {"message": "Error desconocido"}
            logger.error(f"Error en PayPal: {response.status_code} - {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error en PayPal: {error_detail}"
            )
        
        subscription_data = response.json()
        paypal_subscription_id = subscription_data["id"]
        
        logger.info(f"Suscripción creada en PayPal: {paypal_subscription_id}")
        
        # 5. Guardar referencia en Supabase (status='pending_approval' hasta aprobación)
        subscription_record = {
            "user_id": user.id,
            "plan_id": plan["id"],
            "status": "pending_approval",
            "paypal_subscription_id": paypal_subscription_id,
            "current_period_start": None,  # Se actualizará con webhook
            "current_period_end": None
        }
        
        supabase_response = supabase.table("subscriptions").insert(subscription_record).execute()
        
        if not supabase_response.data:
            logger.error("No se pudo guardar la suscripción en Supabase")
            raise HTTPException(status_code=500, detail="Error guardando suscripción en base de datos")
        
        # 6. Obtener approval_url
        approval_url = None
        for link in subscription_data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break
        
        if not approval_url:
            raise HTTPException(status_code=500, detail="No se encontró approval_url en la respuesta de PayPal")
        
        logger.info(f"✅ Suscripción creada exitosamente. Approval URL: {approval_url}")
        
        return {
            "success": True,
            "paypal_subscription_id": paypal_subscription_id,
            "approval_url": approval_url,
            "message": "Redirige al usuario a approval_url para completar el pago"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando suscripción: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creando suscripción: {str(e)}")

@app.get("/api/subscriptions/verify")
async def verify_subscription(
    subscription_id: str = Query(..., description="ID de suscripción de PayPal"),
    user = Depends(get_current_user)
):
    """
    Verifica el estado de una suscripción después del retorno de PayPal
    """
    try:
        # 1. Obtener suscripción de Supabase
        sub_response = supabase.table("subscriptions") \
            .select("*") \
            .eq("paypal_subscription_id", subscription_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not sub_response.data or len(sub_response.data) == 0:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")
        
        subscription = sub_response.data[0]
        
        # 2. Verificar estado en PayPal
        access_token = get_paypal_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error obteniendo estado de PayPal: {response.json()}"
            )
        
        paypal_subscription = response.json()
        paypal_status = paypal_subscription.get("status")
        
        # 3. Actualizar estado en Supabase si cambió
        if paypal_status != subscription["status"]:
            update_data = {"status": paypal_status.lower()}
            
            # Si está activa, actualizar fechas
            if paypal_status == "ACTIVE":
                billing_info = paypal_subscription.get("billing_info", {})
                if billing_info:
                    next_billing_time = billing_info.get("next_billing_time")
                    if next_billing_time:
                        update_data["current_period_start"] = datetime.utcnow().isoformat()
                        # Calcular end basado en el plan
                        plan_response = supabase.table("subscription_plans") \
                            .select("billing_interval") \
                            .eq("id", subscription["plan_id"]) \
                            .single() \
                            .execute()
                        
                        if plan_response.data:
                            interval = plan_response.data.get("billing_interval", "month")
                            if interval == "month":
                                update_data["current_period_end"] = (datetime.utcnow() + timedelta(days=30)).isoformat()
                            elif interval == "year":
                                update_data["current_period_end"] = (datetime.utcnow() + timedelta(days=365)).isoformat()
            
            supabase.table("subscriptions") \
                .update(update_data) \
                .eq("id", subscription["id"]) \
                .execute()
            
            logger.info(f"Suscripción {subscription_id} actualizada a estado: {paypal_status}")
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "status": paypal_status,
            "subscription": paypal_subscription
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando suscripción: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error verificando suscripción: {str(e)}")

# Run server
if __name__ == "__main__":
    print("🚀 Starting BullAnalytics API Server with Supabase...")
    print(f"📊 Supabase URL: {SUPABASE_URL}")
    print("📡 Server: http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
