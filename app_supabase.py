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
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, EmailStr
from cachetools import TTLCache
import uvicorn
import asyncio
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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from email_templates import (
    get_onboarding_email_template,
    get_alert_email_template,
    get_password_reset_email_template,
    get_subscription_confirmation_email_template
)
from cryptography.fernet import Fernet
import hmac
import hashlib
from conexion_iol import ConexionIOL, get_iol_access_token, get_iol_portfolio
from conexion_binance import ConexionBinance, get_binance_portfolio

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
# PayPal URLs - Production: https://bullanalytics.io, Development: http://localhost:8080
# PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "http://localhost:8080/subscription-success.html")
# PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "http://localhost:8080/pricing.html")
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "https://bullanalytics.io/subscription-success.html")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", "https://bullanalytics.io/pricing.html")

# Encryption key for API keys (store securely in environment)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a new key if not exists (for development only, use env var in production)
    ENCRYPTION_KEY = Fernet.generate_key()
    logger.warning("No ENCRYPTION_KEY found, generated a new one. Set this in environment for production!")
else:
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

cipher_suite = Fernet(ENCRYPTION_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="BullAnalytics API",
    description="API for financial asset tracking powered by Yahoo Finance and Supabase",
    version="2.0.0"
)

# CORS configuration
# In production, replace with specific origins
# allow_origins=["*"],  # Development - allows all origins
allow_origins_env = os.getenv("CORS_ORIGINS", "https://bullanalytics.io,http://localhost:8080,http://localhost:8000")
allow_origins = [origin.strip() for origin in allow_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # Production: specific origins, Development: includes localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Cache with 2-minute TTL (120 seconds) for most endpoints
# Earnings calendar uses 24-hour cache (86400 seconds) - handled in endpoint
cache = TTLCache(maxsize=500, ttl=120)

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
    "LOMA": "Loma Negra",
    "CRESY": "Cresud",
    "BBAR": "BBVA Argentina"
    # Note: IRS, TGN, TGS removed - tickers not found or delisted in Yahoo Finance
}

PORTFOLIO_ASSETS = {
    "PFE": "Pfizer",
    "AMD": "AMD",
    "BABA": "Alibaba",
    #"SPY": "SPDR S&P 500 ETF",
    #"QQQ": "Invesco QQQ Trust",
    #"GLD": "SPDR Gold Trust",
    #"DIA": "SPDR Dow Jones Industrial Average ETF",
    #"FXI": "iShares China Large-Cap ETF",
    "MCD": "McDonald's",
    "NFLX": "Netflix",
    "V": "Visa",
    "UBER": "Uber Technologies",
    "DIS": "Walt Disney",
    "SPOT": "Spotify Technology",
    "BAC": "Bank of America",
    #"ABNB": "Airbnb",
    "KO": "Coca-Cola",
    "PLTR": "Palantir Technologies",
    "INTC": "Intel",
    "AVGO": "Broadcom",
    #"WMT": "Walmart",
    "UNH": "UnitedHealth Group",
    "JPM": "JPMorgan Chase",
    "BAYRY": "Bayer",
    "F": "Ford Motor"
}

INDICES_ASSET = {
    "SPY": "SPDR S&P 500 ETF",
    "IWM": "iShares Russell 2000 ETF",
    "QQQ": "Invesco QQQ Trust",
    "GLD": "SPDR Gold Trust",
    "DIA": "SPDR Dow Jones Industrial Average ETF",
    "FXI": "iShares China Large-Cap ETF",
    "NDX": "NASDAQ 100 Index",
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

async def get_optional_user(request: Request):
    """
    Optionally validate JWT token from Supabase Auth and return user or None
    This allows endpoints to work with or without authentication
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        
        # Verify token with Supabase
        try:
            user_response = supabase.auth.get_user(token)
        except Exception:
            return None
        
        if not user_response or not user_response.user:
            return None
        
        logger.info(f"Optional user authenticated: {user_response.user.id}")
        return user_response.user
    except Exception:
        return None

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
    daily_change: Optional[float] = None  # Change in price from previous day
    daily_change_percent: Optional[float] = None  # Percentage change from previous day
    dividends: Optional[float] = None
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
    email: Optional[str] = None  # Email is optional, will use user.email if not provided

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    value: Optional[float] = None

class WatchlistCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assets: Optional[Dict[str, str]] = None  # Dict of ticker -> asset_name

class WatchlistAssetAdd(BaseModel):
    ticker: str
    asset_name: str

class CouponValidate(BaseModel):
    code: str
    plan_name: str

# Broker Connection Models
class BrokerConnectionCreate(BaseModel):
    broker_name: str  # 'IOL' or 'BINANCE'
    api_key: str
    api_secret: Optional[str] = None  # Required for Binance, optional for IOL
    username: Optional[str] = None  # For IOL authentication
    password: Optional[str] = None  # For IOL authentication

class BrokerConnectionUpdate(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_active: Optional[bool] = None

class BrokerConnectionResponse(BaseModel):
    id: str
    broker_name: str
    is_active: bool
    created_at: str
    last_synced: Optional[str] = None

# ============================================
# HELPER FUNCTIONS
# ============================================

# Encryption/Decryption helpers for API keys
def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for secure storage"""
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key for use"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

# Thread pool for timeout operations - aumentado para manejar muchos activos
executor = ThreadPoolExecutor(max_workers=30)

def fetch_with_timeout(func, timeout=20):
    """Execute a function with timeout using thread pool"""
    try:
        future = executor.submit(func)
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        logger.warning(f"Timeout exceeded for operation")
        return None
    except Exception as e:
        logger.error(f"Error in timeout wrapper: {e}")
        return None

def _fetch_ticker_data(ticker: str):
    """Internal function to fetch ticker data with timeout"""
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="max")
    hist_1y = stock.history(period="1y")
    return stock, info, hist, hist_1y

def get_asset_data(ticker: str, name: str) -> Optional[AssetData]:
    """
    Fetch asset data from Yahoo Finance with caching.
    Improved error handling with timeout to prevent worker crashes.
    """
    cache_window = int(datetime.now().timestamp() // 120)
    cache_key = f"{ticker}_{cache_window}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # Fetch data with 20 second timeout
        result = fetch_with_timeout(lambda: _fetch_ticker_data(ticker), timeout=20)
        
        if result is None:
            logger.warning(f"Timeout or error fetching data for {ticker}")
            return None
        
        stock, info, hist, hist_1y = result
        
        # Validate data
        if not info or len(info) == 0:
            logger.warning(f"Ticker {ticker} returned empty info, possibly delisted")
            return None
        
        if hist.empty:
            logger.warning(f"Ticker {ticker} has empty history")
            return None
        
        logo_url = info.get('logo_url') if 'logo_url' in info else None
        
        all_time_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        diff_from_max = (current_price - all_time_high) / all_time_high
        pe_ratio = info.get('trailingPE')
        
        # hist_1y already fetched in _fetch_ticker_data
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
        
        # Daily change (today vs yesterday)
        daily_change = None
        daily_change_percent = None
        if len(hist) >= 2:
            previous_close = hist['Close'].iloc[-2]
            daily_change = float(current_price - previous_close)
            daily_change_percent = float(daily_change / previous_close) if previous_close != 0 else None
        
        # MACD
        macd = None
        if len(hist) >= 26:
            ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = float((ema_12 - ema_26).iloc[-1]) if not (ema_12 - ema_26).empty else None
        
        # Get additional metrics
        revenue = info.get('totalRevenue')
        revenue_growth = info.get('revenueGrowth')
        price_to_book = info.get('priceToBook')
        
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
            daily_change=daily_change,
            daily_change_percent=daily_change_percent,
            revenue=float(revenue) if revenue else None,
            revenue_growth=float(revenue_growth) if revenue_growth else None,
            profit_margin=float(info.get('profitMargins')) if info.get('profitMargins') else None,
            return_on_equity=float(info.get('returnOnEquity')) if info.get('returnOnEquity') else None,
            debt_to_equity=float(info.get('debtToEquity')) if info.get('debtToEquity') else None,
            price_to_book=float(price_to_book) if price_to_book else None,
            beta=float(info.get('beta')) if info.get('beta') else None,
            logo_url=logo_url
        )
        
        cache[cache_key] = asset_data
        return asset_data
        
    except KeyError as e:
        # Missing key in info dict - ticker might be invalid
        logger.warning(f"Missing data key for {ticker}: {e}")
        return None
    except (ValueError, TypeError) as e:
        # Data type errors - skip this ticker
        logger.warning(f"Data type error for {ticker}: {e}")
        return None
    except Exception as e:
        error_msg = str(e).lower()
        # Check for common yfinance errors
        if "404" in error_msg or "not found" in error_msg or "delisted" in error_msg or "timezone" in error_msg:
            logger.warning(f"Ticker {ticker} not available: {e}")
        else:
            logger.error(f"Unexpected error fetching data for {ticker}: {e}", exc_info=True)
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

async def ensure_user_persisted(user_id: str, email: str, auth_source: str, country: Optional[str] = None, date_of_birth: Optional[str] = None) -> Dict[str, Any]:
    """Garantiza que el usuario existe en user_profiles y actualiza country/date_of_birth si se proporcionan"""
    try:
        # Verificar si el usuario ya existe (user_profiles usa 'id' como PK)
        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Usuario {user_id} ya existe en {USER_TABLE_NAME}")
            user_data = response.data[0]
            
            # IMPORTANTE: Siempre actualizar country y date_of_birth si se proporcionan
            # (el trigger crea el registro sin estos campos)
            update_data = {}
            if country and (not user_data.get("country") or user_data.get("country") == ""):
                update_data["country"] = country
            if date_of_birth and not user_data.get("date_of_birth"):
                update_data["date_of_birth"] = date_of_birth
            
            if update_data:
                logger.info(f"Actualizando campos adicionales para usuario existente {user_id}: {update_data}")
                try:
                    supabase.table(USER_TABLE_NAME).update(update_data).eq("id", user_id).execute()
                    # Re-fetch para obtener datos actualizados
                    response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
                    if response.data and len(response.data) > 0:
                        user_data = response.data[0]
                        logger.info(f"Usuario {user_id} actualizado exitosamente con country/date_of_birth")
                except Exception as update_error:
                    logger.warning(f"Error actualizando usuario existente: {str(update_error)}")
            
            # Agregar auth_source al response para compatibilidad
            user_data["auth_source"] = auth_source
            return user_data
        
        # El trigger debería haber creado el registro básico, ahora lo actualizamos
        # Si no existe, intentamos crearlo manualmente
        logger.info(f"Actualizando/creando usuario {user_id} en {USER_TABLE_NAME}")
        
        # Intentar actualizar primero (el trigger ya debería haber creado el registro)
        update_data = {}
        if country:
            update_data["country"] = country
        if date_of_birth:
            update_data["date_of_birth"] = date_of_birth
        
        if update_data:
            try:
                update_response = supabase.table(USER_TABLE_NAME).update(update_data).eq("id", user_id).execute()
                # Verificar si el UPDATE funcionó (puede no devolver datos pero funcionar)
                # Si no hay error, el UPDATE funcionó, verificar que el registro existe
                logger.info(f"UPDATE ejecutado, verificando existencia del usuario")
                response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
                if response.data and len(response.data) > 0:
                    user_data = response.data[0]
                    user_data["auth_source"] = auth_source
                    logger.info(f"Usuario {user_id} actualizado y verificado exitosamente")
                    return user_data
            except Exception as update_error:
                logger.warning(f"Error actualizando usuario (puede que no exista aún): {str(update_error)}")
        
        # Si la actualización falló, verificar si el registro existe (puede que el trigger lo haya creado)
        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            # El registro existe, actualizar con los datos faltantes
            logger.info(f"Usuario {user_id} encontrado, actualizando datos adicionales")
            user_data = response.data[0]
            if update_data:
                try:
                    supabase.table(USER_TABLE_NAME).update(update_data).eq("id", user_id).execute()
                    response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
                    user_data = response.data[0] if response.data else user_data
                except Exception as update_error2:
                    logger.warning(f"Error en segunda actualización: {str(update_error2)}")
            user_data["auth_source"] = auth_source
            return user_data
        
        # Si no existe, esperar un poco más para que el trigger se ejecute
        # Intentar varias veces con esperas incrementales
        import asyncio
        max_attempts = 5
        wait_time = 0.5  # Empezar con 0.5 segundos
        
        for attempt in range(max_attempts):
            await asyncio.sleep(wait_time)
            response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Usuario {user_id} encontrado después de {attempt + 1} intento(s)")
                user_data = response.data[0]
                if update_data:
                    try:
                        supabase.table(USER_TABLE_NAME).update(update_data).eq("id", user_id).execute()
                        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
                        user_data = response.data[0] if response.data else user_data
                    except Exception as update_error3:
                        logger.warning(f"Error en actualización final: {str(update_error3)}")
                user_data["auth_source"] = auth_source
                return user_data
            
            wait_time *= 1.5  # Incrementar el tiempo de espera exponencialmente
        
        # Si aún no existe después de todos los intentos, intentar crear el registro manualmente
        # El trigger puede no haberse ejecutado por varias razones (timing, permisos, etc.)
        logger.warning(f"El trigger no creó el registro después de {max_attempts} intentos. Intentando crear manualmente...")
        try:
            new_user_data = {
                "id": user_id,
                "email": email,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            if country:
                new_user_data["country"] = country
            if date_of_birth:
                new_user_data["date_of_birth"] = date_of_birth
            
            insert_response = supabase.table(USER_TABLE_NAME).insert(new_user_data).execute()
            if insert_response.data and len(insert_response.data) > 0:
                logger.info(f"Usuario {user_id} creado manualmente exitosamente")
                user_data = insert_response.data[0]
                user_data["auth_source"] = auth_source
                return user_data
            else:
                raise Exception(f"La inserción manual no devolvió datos para el usuario {user_id}")
                
        except Exception as insert_error:
            error_msg = str(insert_error)
            logger.error(f"Error al crear usuario manualmente: {error_msg}")
            
            # Si el error es de foreign key, significa que el usuario no existe en auth.users
            if "foreign key" in error_msg.lower() or "violates foreign key" in error_msg.lower() or "23503" in error_msg:
                raise Exception(f"El usuario {user_id} no existe en auth.users. Esto puede ocurrir si: 1) El registro falló, 2) El usuario fue eliminado, o 3) Hay un problema de sincronización. Por favor, intenta registrarte nuevamente.")
            
            # Si falla el INSERT por otra razón, verificar una vez más si el registro existe
            # (por si el trigger se ejecutó mientras intentábamos insertar)
            response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                logger.info(f"Usuario {user_id} encontrado después del intento de inserción manual")
                user_data = response.data[0]
                if update_data:
                    try:
                        supabase.table(USER_TABLE_NAME).update(update_data).eq("id", user_id).execute()
                        response = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
                        user_data = response.data[0] if response.data else user_data
                    except Exception as update_error4:
                        logger.warning(f"Error en actualización post-inserción: {str(update_error4)}")
                user_data["auth_source"] = auth_source
                return user_data
            
            # Si llegamos aquí, hay un problema serio
            raise Exception(f"El trigger no creó el registro en {USER_TABLE_NAME} después de {max_attempts} intentos y la inserción manual también falló: {error_msg}. Por favor, contacta al soporte con el ID de usuario: {user_id}")
        
    except Exception as e:
        logger.error(f"Error en ensure_user_persisted: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al persistir usuario: {str(e)}"
        )

async def create_default_subscription(user_id: str):
    """Crea una suscripción por defecto con plan free (sin trial automático)"""
    try:
        # Obtener el plan "free" (plan gratuito)
        plan_response = supabase.table("subscription_plans").select("*").eq("name", "free").execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            logger.error("Plan 'free' no encontrado")
            return
        
        plan = plan_response.data[0]
        plan_id = plan["id"]
        
        # Calcular fechas (sin trial, solo plan free)
        now = datetime.now(timezone.utc)
        
        # Crear suscripción sin trial (plan free permanente)
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "trial_start": None,
            "trial_end": None,
            "current_period_start": now.isoformat(),
            "current_period_end": None  # Plan free no tiene fecha de fin
        }
        
        subscription_response = supabase.table("subscriptions").insert(subscription_data).execute()
        
        if subscription_response.data:
            logger.info(f"Suscripción free creada para usuario {user_id}")
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
    confirm_password: str
    country: str
    date_of_birth: str  # Format: YYYY-MM-DD

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: Optional[str] = None  # Token puede venir del header o del body
    password: str
    confirm_password: str

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

async def fetch_asset_async(ticker: str, name: str):
    """Fetch asset data asynchronously"""
    loop = asyncio.get_event_loop()
    try:
        asset_data = await loop.run_in_executor(executor, get_asset_data, ticker, name)
        return asset_data
    except Exception as e:
        logger.warning(f"Error fetching {ticker}: {e}")
        return None

@app.get("/api/tracking-assets", response_model=List[AssetData])
async def get_tracking_assets():
    """Get tracking assets data - parallel processing"""
    tasks = [fetch_asset_async(ticker, name) for ticker, name in TRACKING_ASSETS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None values and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    return valid_results

@app.get("/api/portfolio-assets", response_model=List[AssetData])
async def get_portfolio_assets():
    """Get portfolio assets data - parallel processing"""
    tasks = [fetch_asset_async(ticker, name) for ticker, name in PORTFOLIO_ASSETS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None values and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    return valid_results

@app.get("/api/crypto-assets", response_model=List[AssetData])
async def get_crypto_assets():
    """Get crypto assets data - parallel processing"""
    tasks = [fetch_asset_async(ticker, name) for ticker, name in CRYPTO_ASSETS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None values and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    return valid_results

@app.get("/api/argentina-assets", response_model=List[AssetData])
async def get_argentina_assets():
    """Get Argentina assets data - parallel processing"""
    tasks = [fetch_asset_async(ticker, name) for ticker, name in ARGENTINA_ASSETS.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None values and exceptions
    valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
    return valid_results

@app.get("/api/asset/{ticker}/history")
async def get_asset_history(ticker: str, period: str = "1y", interval: str = "1d"):
    """Get historical price data for an asset"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")
        
        # Convert to list of dicts
        history_data = []
        for date, row in hist.iterrows():
            history_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": float(row['Volume'])
            })
        
        return history_data
        
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching history for {ticker}")

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
# EARNINGS CALENDAR ENDPOINTS
# ============================================

@app.get("/api/earnings-calendar")
async def get_earnings_calendar(
    year: Optional[int] = Query(None, description="Year to filter (default: current year)"),
    month: Optional[int] = Query(None, description="Month to filter (1-12, default: current month)")
):
    """
    Get earnings calendar for all tracked assets.
    Returns earnings dates grouped by date.
    Cache: 24 hours
    """
    try:
        # Use current year/month if not provided
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        # Validate date range: only allow last 2 months and next 4 months
        current_date = datetime(now.year, now.month, 1)
        target_date = datetime(target_year, target_month, 1)
        
        # Calculate months difference
        months_diff = (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month)
        
        if months_diff < -2 or months_diff > 4:
            raise HTTPException(
                status_code=400,
                detail=f"Solo se pueden visualizar los últimos 2 meses y los próximos 4 meses. Mes solicitado: {target_month}/{target_year}"
            )
        
        # Cache key with 24 hour TTL (86400 seconds)
        cache_key = f"earnings_calendar_{target_year}_{target_month}_{int(now.timestamp() // 86400)}"
        
        if cache_key in cache:
            return cache[cache_key]
        
        # Combine all assets
        all_assets = {**TRACKING_ASSETS, **PORTFOLIO_ASSETS, **ARGENTINA_ASSETS}
        
        earnings_events = []
        
        for ticker, name in all_assets.items():
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Try to get earnings date from info
                earnings_date = None
                
                # Check multiple possible fields for earnings date
                if 'earningsDate' in info and info.get('earningsDate'):
                    earnings_date = info.get('earningsDate')
                elif 'nextFiscalYearEnd' in info and info.get('nextFiscalYearEnd'):
                    # Sometimes earnings date is in nextFiscalYearEnd
                    earnings_date = info.get('nextFiscalYearEnd')
                elif 'mostRecentQuarter' in info and info.get('mostRecentQuarter'):
                    # Try to calculate next earnings from most recent quarter
                    most_recent = info.get('mostRecentQuarter')
                    if most_recent:
                        try:
                            # Parse timestamp and add ~3 months for next quarter
                            if isinstance(most_recent, (int, float)):
                                earnings_date = datetime.fromtimestamp(most_recent) + timedelta(days=90)
                            else:
                                earnings_date = datetime.strptime(str(most_recent), '%Y-%m-%d') + timedelta(days=90)
                        except:
                            pass
                
                # Also try calendar attribute
                if not earnings_date:
                    try:
                        calendar = stock.calendar
                        if calendar is not None and not calendar.empty:
                            # Get the next earnings date from calendar
                            if 'Earnings Date' in calendar.columns:
                                earnings_date = calendar['Earnings Date'].iloc[0]
                            elif len(calendar) > 0:
                                # Try first row
                                earnings_date = calendar.index[0] if hasattr(calendar.index[0], 'date') else None
                    except Exception as e:
                        logger.debug(f"Error getting calendar for {ticker}: {e}")
                
                # Convert earnings_date to datetime if it's not None
                if earnings_date:
                    if isinstance(earnings_date, (int, float)):
                        earnings_date = datetime.fromtimestamp(earnings_date)
                    elif isinstance(earnings_date, str):
                        try:
                            # Try different date formats
                            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S%z']:
                                try:
                                    earnings_date = datetime.strptime(earnings_date, fmt)
                                    break
                                except:
                                    continue
                            if isinstance(earnings_date, str):
                                # If still string, try to parse as timestamp
                                earnings_date = datetime.fromtimestamp(float(earnings_date))
                        except:
                            logger.debug(f"Could not parse earnings_date for {ticker}: {earnings_date}")
                            continue
                    
                    # Filter by target month/year
                    if earnings_date.year == target_year and earnings_date.month == target_month:
                        # Check if date is in the past to add link to earnings
                        is_past = earnings_date < now
                        earnings_link = None
                        
                        if is_past:
                            # Generate link to Yahoo Finance earnings page
                            earnings_link = f"https://finance.yahoo.com/quote/{ticker}/financials"
                        
                        earnings_events.append({
                            "ticker": ticker,
                            "name": name,
                            "date": earnings_date.strftime("%Y-%m-%d"),
                            "datetime": earnings_date.isoformat(),
                            "day": earnings_date.day,
                            "month": earnings_date.month,
                            "year": earnings_date.year,
                            "is_past": is_past,
                            "earnings_link": earnings_link
                        })
            except Exception as e:
                logger.debug(f"Error fetching earnings for {ticker}: {e}")
                continue
        
        # Group by date
        events_by_date = {}
        for event in earnings_events:
            date_key = event["date"]
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)
        
        result = {
            "year": target_year,
            "month": target_month,
            "events": events_by_date,
            "total_events": len(earnings_events)
        }
        
        # Cache for 24 hours (86400 seconds) - cache key already includes day
        cache[cache_key] = result
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching earnings calendar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching earnings calendar: {str(e)}")

@app.get("/api/asset/{ticker}/analyst-insights")
async def get_analyst_insights(ticker: str):
    """
    Get analyst insights for an asset using yfinance Analysis class.
    Includes recommendations, price targets, sentiment, and earnings expectations.
    """
    try:
        cache_key = f"analyst_insights_{ticker}_{int(datetime.now().timestamp() // 3600)}"
        
        if cache_key in cache:
            return cache[cache_key]
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Use yfinance Analysis class for better data
        analysis = stock.analysis
        
        # Get analyst recommendations from recommendations DataFrame
        recommendations = {
            'strongBuy': 0,
            'buy': 0,
            'hold': 0,
            'underperform': 0,
            'sell': 0,
        }
        
        try:
            # Try to get recommendations DataFrame
            recs_df = stock.recommendations
            if recs_df is not None and not recs_df.empty:
                # Get last 4 months of recommendations
                now = datetime.now()
                four_months_ago = now - timedelta(days=120)
                
                # Filter by date if possible
                if hasattr(recs_df.index, 'date'):
                    recent_recs = recs_df[recs_df.index >= four_months_ago]
                else:
                    # Take last 4 months worth of data
                    recent_recs = recs_df.tail(4) if len(recs_df) > 4 else recs_df
                
                # Count recommendations by type
                for _, row in recent_recs.iterrows():
                    # Yahoo Finance recommendations are usually in a 'To Grade' column
                    if 'To Grade' in row:
                        grade = str(row['To Grade']).upper()
                        if 'STRONG BUY' in grade or 'STRONGBUY' in grade:
                            recommendations['strongBuy'] += 1
                        elif 'BUY' in grade:
                            recommendations['buy'] += 1
                        elif 'HOLD' in grade or 'NEUTRAL' in grade:
                            recommendations['hold'] += 1
                        elif 'UNDERPERFORM' in grade or 'UNDER PERFORM' in grade:
                            recommendations['underperform'] += 1
                        elif 'SELL' in grade:
                            recommendations['sell'] += 1
        except Exception as e:
            logger.debug(f"Error getting recommendations DataFrame for {ticker}: {e}")
        
        # Fallback to info fields if DataFrame didn't work
        if sum(recommendations.values()) == 0:
            # Try recommendationMean field (sometimes it's a dict)
            rec_mean = info.get('recommendationMean')
            if isinstance(rec_mean, dict):
                recommendations['strongBuy'] = rec_mean.get('strongBuy', 0)
                recommendations['buy'] = rec_mean.get('buy', 0)
                recommendations['hold'] = rec_mean.get('hold', 0)
                recommendations['underperform'] = rec_mean.get('underperform', 0)
                recommendations['sell'] = rec_mean.get('sell', 0)
            elif isinstance(rec_mean, (int, float)):
                # If it's a number, distribute it (this is less accurate)
                total = int(rec_mean) if rec_mean else 0
                if total > 0:
                    recommendations['hold'] = total  # Default to hold if we only have a number
            
            # Try recommendationKey field as last resort
            if sum(recommendations.values()) == 0:
                rec_key = str(info.get('recommendationKey', '')).lower()
                if 'strong buy' in rec_key or 'strongbuy' in rec_key:
                    recommendations['strongBuy'] = 1
                elif 'buy' in rec_key:
                    recommendations['buy'] = 1
                elif 'hold' in rec_key or 'neutral' in rec_key:
                    recommendations['hold'] = 1
                elif 'underperform' in rec_key or 'under perform' in rec_key:
                    recommendations['underperform'] = 1
                elif 'sell' in rec_key:
                    recommendations['sell'] = 1
        
        # Get price targets using Analysis class
        price_targets = {}
        try:
            price_targets = analysis.analyst_price_targets
        except Exception as e:
            logger.debug(f"Error getting price targets from Analysis for {ticker}: {e}")
            # Fallback to info
            price_targets = {
                'low': info.get('targetLowPrice'),
                'high': info.get('targetHighPrice'),
                'mean': info.get('targetMeanPrice'),
                'median': info.get('targetMedianPrice'),
                'current': info.get('currentPrice') or info.get('regularMarketPrice')
            }
        
        current_price = price_targets.get('current') or info.get('currentPrice') or info.get('regularMarketPrice')
        
        # Get earnings estimates using Analysis class
        last_quarter_expected = None
        last_annual_expected = None
        last_quarter_earnings = None
        last_annual_earnings = None
        
        # New data structures for graphs
        earnings_trend = []
        financials_chart = []
        
        try:
            # Get earnings estimates
            earnings_estimate = analysis.earnings_estimate
            if earnings_estimate is not None and not earnings_estimate.empty:
                # Get most recent quarter estimate
                if 'currentQuarter' in earnings_estimate.index:
                    last_quarter_expected = earnings_estimate.loc['currentQuarter', 'avgEstimate'] if 'avgEstimate' in earnings_estimate.columns else None
                elif len(earnings_estimate) > 0:
                    # Get first row (most recent)
                    last_quarter_expected = earnings_estimate.iloc[0].get('avgEstimate') if 'avgEstimate' in earnings_estimate.columns else None
                
                # Get current year estimate
                if 'currentYear' in earnings_estimate.index:
                    last_annual_expected = earnings_estimate.loc['currentYear', 'avgEstimate'] if 'avgEstimate' in earnings_estimate.columns else None
        except Exception as e:
            logger.debug(f"Error getting earnings estimates for {ticker}: {e}")
        
        # Get earnings history (actual vs expected) for Trend Graph
        try:
            earnings_history = analysis.earnings_history
            if earnings_history is not None and not earnings_history.empty:
                # Sort by index or date if available to ensure chronological order
                # Usually it's indexed by date, but let's check
                history_df = earnings_history.copy()
                # Take last 4 quarters
                recent_history = history_df.tail(4)
                
                for index, row in recent_history.iterrows():
                    period_name = str(index).split(' ')[0] if hasattr(index, 'strftime') else str(index)
                    # Try to format date nicely if it's a date
                    try:
                        if hasattr(index, 'strftime'):
                            period_name = index.strftime('%b %y')
                    except:
                        pass
                        
                    earnings_trend.append({
                        "period": period_name,
                        "estimate": float(row['epsEstimate']) if row.get('epsEstimate') is not None else 0,
                        "actual": float(row['epsActual']) if row.get('epsActual') is not None else 0,
                        "difference": float(row['epsDifference']) if row.get('epsDifference') is not None else 0
                    })
                
                # Get most recent quarter for summary
                most_recent = earnings_history.iloc[-1] if len(earnings_history) > 0 else None
                if most_recent is not None:
                    # Get actual earnings
                    if 'epsActual' in most_recent:
                        last_quarter_earnings = float(most_recent['epsActual']) if most_recent['epsActual'] is not None else None
                    elif 'epsEstimate' in most_recent:
                        # Use estimate if actual not available
                        last_quarter_expected = float(most_recent['epsEstimate']) if most_recent['epsEstimate'] is not None else None
        except Exception as e:
            logger.debug(f"Error getting earnings history for {ticker}: {e}")
        
        # Fallback: Get earnings from financials if Analysis didn't work
        if last_quarter_earnings is None or last_annual_earnings is None:
            try:
                financials = stock.financials
                quarterly_financials = stock.quarterly_financials
                
                if quarterly_financials is not None and not quarterly_financials.empty:
                    if 'Net Income' in quarterly_financials.index:
                        last_quarter_earnings = float(quarterly_financials.loc['Net Income'].iloc[-1]) if not quarterly_financials.loc['Net Income'].empty else None
                    elif 'Total Revenue' in quarterly_financials.index:
                        last_quarter_earnings = float(quarterly_financials.loc['Total Revenue'].iloc[-1]) if not quarterly_financials.loc['Total Revenue'].empty else None
                    
                    # Prepare Financials Chart (Revenue vs Earnings)
                    # Get last 4 quarters
                    quarters = quarterly_financials.columns[:4] # Usually columns are dates descending
                    for date in reversed(quarters): # Process in chronological order
                        revenue = 0
                        earnings = 0
                        if 'Total Revenue' in quarterly_financials.index:
                            revenue = float(quarterly_financials.loc['Total Revenue'][date])
                        if 'Net Income' in quarterly_financials.index:
                            earnings = float(quarterly_financials.loc['Net Income'][date])
                        
                        period_name = date.strftime('%Q %Y') if hasattr(date, 'strftime') else str(date)
                        try:
                            # Try to convert to Q{q} FY{yy} format approximation
                            # Just use Month Year for simplicity or Quarter Year
                            if hasattr(date, 'month') and hasattr(date, 'year'):
                                q = (date.month - 1) // 3 + 1
                                period_name = f"Q{q} {str(date.year)[2:]}"
                        except:
                            pass

                        financials_chart.append({
                            "period": period_name,
                            "revenue": revenue,
                            "earnings": earnings
                        })

                if financials is not None and not financials.empty:
                    if 'Net Income' in financials.index:
                        last_annual_earnings = float(financials.loc['Net Income'].iloc[-1]) if not financials.loc['Net Income'].empty else None
                    elif 'Total Revenue' in financials.index:
                        last_annual_earnings = float(financials.loc['Total Revenue'].iloc[-1]) if not financials.loc['Total Revenue'].empty else None
            except Exception as e:
                logger.debug(f"Error fetching earnings data from financials for {ticker}: {e}")
        
        # Get revenue estimates
        try:
            revenue_estimate = analysis.revenue_estimate
            if revenue_estimate is not None and not revenue_estimate.empty:
                # Use revenue estimates if earnings estimates not available
                if last_quarter_expected is None and 'currentQuarter' in revenue_estimate.index:
                    last_quarter_expected = revenue_estimate.loc['currentQuarter', 'avgEstimate'] if 'avgEstimate' in revenue_estimate.columns else None
                if last_annual_expected is None and 'currentYear' in revenue_estimate.index:
                    last_annual_expected = revenue_estimate.loc['currentYear', 'avgEstimate'] if 'avgEstimate' in revenue_estimate.columns else None
        except Exception as e:
            logger.debug(f"Error getting revenue estimates for {ticker}: {e}")
        
        # Get top analyst (simulated - Yahoo Finance doesn't provide this directly)
        top_analyst = info.get('recommendationKey', 'N/A')
        analyst_score = 45  # Default score
        
        # Calculate sentiment based on recommendations
        total_recs = sum(recommendations.values())
        if total_recs > 0:
            sentiment_score = (
                recommendations['strongBuy'] * 5 +
                recommendations['buy'] * 4 +
                recommendations['hold'] * 3 +
                recommendations['underperform'] * 2 +
                recommendations['sell'] * 1
            ) / total_recs
            
            if sentiment_score >= 4.5:
                sentiment = 'Muy Alcista'
                sentiment_color = 'green'
            elif sentiment_score >= 3.5:
                sentiment = 'Alcista'
                sentiment_color = 'lightgreen'
            elif sentiment_score >= 2.5:
                sentiment = 'Neutral'
                sentiment_color = 'yellow'
            elif sentiment_score >= 1.5:
                sentiment = 'Bajista'
                sentiment_color = 'orange'
            else:
                sentiment = 'Muy Bajista'
                sentiment_color = 'red'
        else:
            sentiment = 'Sin Datos'
            sentiment_color = 'gray'
        
        # Market expectation - use business summary from info
        market_expectation = info.get('longBusinessSummary', '')[:200] if info.get('longBusinessSummary') else "Los analistas esperan resultados sólidos basados en el crecimiento de ingresos y la expansión del mercado."
        
        result = {
            "ticker": ticker,
            "name": info.get('longName') or info.get('shortName', ticker),
            "current_price": float(current_price) if current_price else None,
            "top_analyst": {
                "name": "Goldman Sachs",  # Simulated
                "score": analyst_score,
                "latest_rating": top_analyst.upper() if top_analyst else "NEUTRAL"
            },
            "price_targets": {
                "low": float(price_targets.get('low') or price_targets.get('Low')) if price_targets.get('low') or price_targets.get('Low') else None,
                "high": float(price_targets.get('high') or price_targets.get('High')) if price_targets.get('high') or price_targets.get('High') else None,
                "average": float(price_targets.get('mean') or price_targets.get('Mean') or price_targets.get('median') or price_targets.get('Median')) if (price_targets.get('mean') or price_targets.get('Mean') or price_targets.get('median') or price_targets.get('Median')) else None,
                "current": float(current_price) if current_price else None
            },
            "recommendations": recommendations,
            "total_recommendations": total_recs,
            "sentiment": {
                "value": sentiment,
                "color": sentiment_color,
                "score": sentiment_score if total_recs > 0 else 3
            },
            "market_expectation": market_expectation,
            "earnings": {
                "last_quarter": {
                    "actual": last_quarter_earnings,
                    "expected": last_quarter_expected
                },
                "last_annual": {
                    "actual": last_annual_earnings,
                    "expected": last_annual_expected
                },
                "trend": earnings_trend,
                "financials_chart": financials_chart
            }
        }
        
        cache[cache_key] = result
        logger.info(f"Successfully fetched analyst insights for {ticker}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching analyst insights for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching analyst insights: {str(e)}")

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
        
        # Use user's email from authentication
        user_email = user.email if hasattr(user, 'email') and user.email else None
        if not user_email:
            raise HTTPException(status_code=400, detail="No se pudo obtener el email del usuario autenticado")
        
        rule_data = {
            "user_id": user.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "ticker": rule.ticker,
            "value_threshold": rule.value,
            "email": user_email,  # Use authenticated user's email
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

class ChatMessage(BaseModel):
    message: str
    email: Optional[str] = None

@app.post("/api/rules/chat")
async def chat_create_rule(chat_message: ChatMessage, request: Request):
    """Create a rule from natural language using AI - Authentication optional"""
    try:
        # Try to get optional user
        user = await get_optional_user(request)
        
        # Initialize Groq client
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
        
        client = Groq(api_key=api_key)
        
        # System prompt
        system_prompt = """Eres un asistente que interpreta lenguaje natural y lo convierte en JSON para crear reglas de alertas financieras.

Tu objetivo es extraer los siguientes campos del mensaje del usuario:
- name: Un nombre descriptivo para la regla (en español)
- type: El tipo de regla. Opciones válidas: "price_below", "price_above", "pe_below", "pe_above", "max_distance"
- ticker: El símbolo del activo (ej: NVDA, AAPL, BTC-USD, META)
- value: El valor numérico de referencia (porcentaje o número según el tipo)
- email: El email del usuario (opcional, solo si se menciona explícitamente en el mensaje)

Tipos de reglas:
- "price_below": Precio debajo de un valor específico
- "price_above": Precio encima de un valor específico
- "pe_below": P/E Ratio debajo de un valor
- "pe_above": P/E Ratio encima de un valor
- "max_distance": Distancia porcentual del máximo histórico (valor negativo indica debajo del máximo)

Ejemplos:
Input: "Cuando NVIDIA esté un 25% debajo de su máximo histórico"
Output: {"name": "Alerta: NVIDIA se encuentra un 25% debajo de su máximo histórico", "type": "max_distance", "ticker": "NVDA", "value": 25}

Input: "Notifícame cuando Apple tenga un P/E ratio debajo de 25"
Output: {"name": "Alerta: Apple P/E ratio debajo de 25", "type": "pe_below", "ticker": "AAPL", "value": 25}

Input: "Quiero una alerta cuando Bitcoin esté por encima de $50,000"
Output: {"name": "Alerta: Bitcoin por encima de $50,000", "type": "price_above", "ticker": "BTC-USD", "value": 50000}

Input: "avisame cuando meta llegue a un per de 40"
Output: {"name": "Alerta: Meta P/E ratio de 40", "type": "pe_above", "ticker": "META", "value": 40}

Responde SOLO con un JSON válido, sin texto adicional. Si falta información crítica (como el ticker), incluye un campo "error" con el mensaje explicando qué falta."""

        # User prompt
        user_prompt = chat_message.message
        if chat_message.email:
            user_prompt += f"\n\nEmail del usuario: {chat_message.email}"

        # Call Groq API
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise HTTPException(status_code=500, detail=f"Error calling Groq API: {str(e)}")

        # Parse response
        response_content = completion.choices[0].message.content.strip()
        
        # Try to extract JSON from response (in case there's extra text)
        # Look for JSON object with balanced braces
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(response_content):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    response_content = response_content[start_idx:i+1]
                    break
        
        # If no balanced JSON found, try regex as fallback
        if start_idx == -1 or brace_count != 0:
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                response_content = json_match.group(0)
        
        try:
            rule_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, response: {response_content}")
            return {
                "success": False,
                "error": f"No se pudo interpretar la respuesta del AI. Por favor, intenta ser más específico con tu solicitud.",
                "raw_response": response_content
            }

        # Check for errors
        if "error" in rule_data:
            return {"success": False, "error": rule_data["error"], "raw_response": response_content}

        # Validate required fields
        required_fields = ["name", "type", "ticker", "value"]
        missing_fields = [field for field in required_fields if field not in rule_data]
        if missing_fields:
            return {
                "success": False,
                "error": f"Faltan campos requeridos: {', '.join(missing_fields)}",
                "raw_response": response_content
            }

        # Validate type
        valid_types = ["price_below", "price_above", "pe_below", "pe_above", "max_distance"]
        if rule_data["type"] not in valid_types:
            return {
                "success": False,
                "error": f"Tipo de regla inválido: {rule_data['type']}. Tipos válidos: {', '.join(valid_types)}",
                "raw_response": response_content
            }

        # Use user's email from authentication if available, otherwise use provided email
        if user:
            email = user.email if hasattr(user, 'email') and user.email else None
            if not email:
                return {
                    "success": False,
                    "error": "No se pudo obtener el email del usuario autenticado.",
                    "raw_response": response_content
                }
        else:
            # No user authenticated, use provided email or try to extract from rule_data
            email = chat_message.email or rule_data.get("email")
            if not email:
                return {
                    "success": False,
                    "error": "Se requiere autenticación o proporcionar un email para las notificaciones.",
                    "raw_response": response_content
                }

        # Map type to rule_type (for Supabase schema)
        type_mapping = {
            "price_below": "price_below",
            "price_above": "price_above",
            "pe_below": "pe_below",
            "pe_above": "pe_above",
            "max_distance": "max_distance"
        }
        rule_type = type_mapping.get(rule_data["type"], rule_data["type"])

        # Create the rule
        if user:
            # User is authenticated, save to Supabase
            try:
                # Check user's plan limits
                try:
                    check_result = supabase.rpc("check_user_plan_limit", {
                        "p_user_id": user.id,
                        "p_limit_type": "max_rules"
                    }).execute()
                    
                    can_create = check_result.data if check_result.data is not None else True
                    
                    if not can_create:
                        return {
                            "success": False,
                            "error": "Has alcanzado el límite de reglas de tu plan. Actualiza tu suscripción."
                        }
                except Exception as rpc_error:
                    logger.warning(f"Error checking plan limit, continuando: {str(rpc_error)}")
                
                rule_data_db = {
                    "user_id": user.id,
                    "name": rule_data["name"],
                    "rule_type": rule_type,
                    "ticker": rule_data["ticker"].upper(),
                    "value_threshold": rule_data["value"],
                    "email": email,
                    "is_active": True
                }
                
                response = supabase.table("rules").insert(rule_data_db).execute()
                
                if not response.data or len(response.data) == 0:
                    return {
                        "success": False,
                        "error": "No se pudo crear la regla en la base de datos."
                    }
                
                created_rule = response.data[0]
                return {
                    "success": True,
                    "message": "Regla creada exitosamente",
                    "rule": {
                        "id": created_rule.get("id"),
                        "name": created_rule.get("name"),
                        "rule_type": created_rule.get("rule_type"),
                        "ticker": created_rule.get("ticker"),
                        "value": created_rule.get("value_threshold"),
                        "email": created_rule.get("email")
                    }
                }
            except Exception as e:
                logger.error(f"Error creating rule in Supabase: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error al crear la regla: {str(e)}"
                }
        else:
            # No user authenticated, return rule data for frontend to handle
            # (Frontend can save to localStorage or prompt for login)
            return {
                "success": True,
                "message": "Regla interpretada exitosamente. Por favor, inicia sesión para guardarla.",
                "rule": {
                    "name": rule_data["name"],
                    "rule_type": rule_type,
                    "ticker": rule_data["ticker"].upper(),
                    "value": rule_data["value"],
                    "email": email
                },
                "requires_auth": True
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_create_rule: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Error al procesar la solicitud: {str(e)}"
        }

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
# ASSET SEARCH ENDPOINT
# ============================================

@app.get("/api/search-assets")
async def search_assets(query: str = Query(..., description="Search query for assets")):
    """Search for assets using Yahoo Finance autocomplete API - No authentication required"""
    if not query or len(query) < 2:
        return []
    
    try:
        import urllib.parse
        
        # Yahoo Finance autocomplete endpoint
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&quotesCount=10&newsCount=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Extract quotes from the response
            if 'quotes' in data:
                for quote in data['quotes']:
                    # Filter out invalid symbols
                    symbol = quote.get('symbol', '')
                    if symbol and '.' not in symbol:  # Exclude symbols with dots (like options)
                        results.append({
                            "symbol": symbol,
                            "name": quote.get('longname') or quote.get('shortname', '') or symbol,
                            "exchange": quote.get('exchange', ''),
                            "type": quote.get('quoteType', 'EQUITY'),
                            "sector": quote.get('sector', ''),
                            "industry": quote.get('industry', '')
                        })
            
            return results[:10]  # Limit to 10 results
        
        logger.warning(f"Yahoo Finance API returned status {response.status_code}")
        return []
        
    except requests.exceptions.Timeout:
        logger.error("Timeout searching assets")
        return []
    except Exception as e:
        logger.error(f"Error searching assets: {e}", exc_info=True)
        return []

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
    """Create a new watchlist with assets"""
    try:
        # Create watchlist
        watchlist_data = {
            "user_id": user.id,
            "name": watchlist.name,
            "description": watchlist.description or ""
        }
        
        watchlist_response = supabase.table("watchlists").insert(watchlist_data).execute()
        
        if not watchlist_response.data or len(watchlist_response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create watchlist")
        
        watchlist_id = watchlist_response.data[0]['id']
        
        # Add assets to watchlist if provided
        if watchlist.assets:
            assets_to_add = []
            for ticker, asset_name in watchlist.assets.items():
                assets_to_add.append({
                    "watchlist_id": watchlist_id,
                    "ticker": ticker.upper(),
                    "asset_name": asset_name
                })
            
            if assets_to_add:
                supabase.table("watchlist_assets").insert(assets_to_add).execute()
        
        # Return watchlist with assets
        response = supabase.table("watchlists") \
            .select("*, watchlist_assets(*)") \
            .eq("id", watchlist_id) \
            .execute()
        
        return {
            "message": "Watchlist created successfully",
            "watchlist": response.data[0] if response.data else watchlist_response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating watchlist: {str(e)}", exc_info=True)
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

@app.get("/api/watchlists/{watchlist_id}/assets-data")
async def get_watchlist_assets_data(watchlist_id: str, user = Depends(get_current_user)):
    """Get financial data for all assets in a watchlist"""
    try:
        # Verify watchlist belongs to user
        watchlist_response = supabase.table("watchlists") \
            .select("*, watchlist_assets(*)") \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        watchlist = watchlist_response.data[0]
        watchlist_assets = watchlist.get('watchlist_assets', [])
        
        # Get financial data for each asset
        assets_data = []
        for asset in watchlist_assets:
            ticker = asset.get('ticker')
            asset_name = asset.get('asset_name', ticker)
            
            if ticker:
                asset_data = get_asset_data(ticker, asset_name)
                if asset_data:
                    assets_data.append(asset_data)
        
        return assets_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching watchlist assets data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching watchlist assets data: {str(e)}")

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

@app.delete("/api/watchlists/{watchlist_id}/assets/{ticker}")
async def delete_asset_from_watchlist(
    watchlist_id: str,
    ticker: str,
    user = Depends(get_current_user)
):
    """Remove an asset from a watchlist"""
    try:
        # Verify watchlist belongs to user
        watchlist_response = supabase.table("watchlists") \
            .select("id") \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        # Delete the asset
        response = supabase.table("watchlist_assets") \
            .delete() \
            .eq("watchlist_id", watchlist_id) \
            .eq("ticker", ticker.upper()) \
            .execute()
        
        return {"message": "Asset removed from watchlist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing asset: {str(e)}")

@app.patch("/api/watchlists/{watchlist_id}")
async def update_watchlist(
    watchlist_id: str,
    watchlist_update: Dict[str, Any],
    user = Depends(get_current_user)
):
    """Update a watchlist (name, description, etc.)"""
    try:
        # Verify watchlist belongs to user
        watchlist_response = supabase.table("watchlists") \
            .select("id") \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not watchlist_response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        # Prepare update data
        update_data = {}
        if "name" in watchlist_update:
            update_data["name"] = watchlist_update["name"]
        if "description" in watchlist_update:
            update_data["description"] = watchlist_update["description"]
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update watchlist
        response = supabase.table("watchlists") \
            .update(update_data) \
            .eq("id", watchlist_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        
        return {
            "message": "Watchlist updated successfully",
            "watchlist": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating watchlist: {str(e)}")

# ============================================
# BROKER CONNECTIONS ENDPOINTS
# ============================================

@app.post("/api/broker-connections", tags=["Broker"])
async def create_broker_connection(
    connection: BrokerConnectionCreate,
    user = Depends(get_current_user)
):
    """Create a new broker connection for paid users"""
    try:
        # Check if user has active paid subscription
        sub_response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not sub_response.data:
            raise HTTPException(
                status_code=403,
                detail="Broker connections require an active paid subscription"
            )
        
        plan = sub_response.data[0].get("subscription_plans", {})
        if plan.get("name") == "free":
            raise HTTPException(
                status_code=403,
                detail="Broker connections are only available for Plus and Pro plans"
            )
        
        # Validate broker name
        if connection.broker_name not in ["IOL", "BINANCE"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid broker. Supported brokers: IOL, BINANCE"
            )
        
        # Validate broker-specific credentials using new connection modules
        if connection.broker_name == "IOL":
            if not connection.username or not connection.password:
                raise HTTPException(
                    status_code=400,
                    detail="IOL requires username and password"
                )
            # Test IOL connection using new module
            conexion_iol = ConexionIOL(connection.username, connection.password)
            if not await conexion_iol.validar_credenciales():
                raise HTTPException(
                    status_code=400,
                    detail="Failed to authenticate with IOL. Please check your credentials."
                )
        
        elif connection.broker_name == "BINANCE":
            if not connection.api_key or not connection.api_secret:
                raise HTTPException(
                    status_code=400,
                    detail="Binance requires api_key and api_secret"
                )
            # Test Binance connection using new module
            conexion_binance = ConexionBinance(connection.api_key, connection.api_secret)
            if not await conexion_binance.validar_credenciales():
                raise HTTPException(
                    status_code=400,
                    detail="Failed to connect to Binance. Please check your API credentials."
                )
        
        # Check if connection already exists
        existing = supabase.table("broker_connections") \
            .select("*") \
            .eq("user_id", user.id) \
            .eq("broker_name", connection.broker_name) \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=400,
                detail=f"Connection to {connection.broker_name} already exists. Please update or delete the existing one."
            )
        
        # Encrypt sensitive data
        encrypted_api_key = encrypt_api_key(connection.api_key) if connection.api_key else None
        encrypted_api_secret = encrypt_api_key(connection.api_secret) if connection.api_secret else None
        encrypted_username = encrypt_api_key(connection.username) if connection.username else None
        encrypted_password = encrypt_api_key(connection.password) if connection.password else None
        
        # Create connection
        connection_data = {
            "user_id": user.id,
            "broker_name": connection.broker_name,
            "api_key_encrypted": encrypted_api_key,
            "api_secret_encrypted": encrypted_api_secret,
            "username_encrypted": encrypted_username,
            "password_encrypted": encrypted_password,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("broker_connections").insert(connection_data).execute()
        
        return {
            "message": "Broker connection created successfully",
            "connection": {
                "id": response.data[0]["id"],
                "broker_name": response.data[0]["broker_name"],
                "is_active": response.data[0]["is_active"],
                "created_at": response.data[0]["created_at"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating broker connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating broker connection: {str(e)}")

@app.get("/api/broker-connections", tags=["Broker"])
async def get_broker_connections(user = Depends(get_current_user)):
    """Get all broker connections for the authenticated user"""
    try:
        response = supabase.table("broker_connections") \
            .select("id, broker_name, is_active, created_at, last_synced") \
            .eq("user_id", user.id) \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data
    
    except Exception as e:
        logger.error(f"Error fetching broker connections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching broker connections: {str(e)}")

@app.delete("/api/broker-connections/{connection_id}", tags=["Broker"])
async def delete_broker_connection(connection_id: str, user = Depends(get_current_user)):
    """Delete a broker connection"""
    try:
        # Verify connection belongs to user
        connection_response = supabase.table("broker_connections") \
            .select("*") \
            .eq("id", connection_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not connection_response.data:
            raise HTTPException(status_code=404, detail="Broker connection not found")
        
        # Delete connection
        supabase.table("broker_connections").delete().eq("id", connection_id).execute()
        
        return {"message": "Broker connection deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting broker connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting broker connection: {str(e)}")

@app.get("/api/broker-connections/{connection_id}/portfolio", tags=["Broker"])
async def get_broker_portfolio(connection_id: str, user = Depends(get_current_user)):
    """Get portfolio from a connected broker"""
    try:
        # Get connection
        connection_response = supabase.table("broker_connections") \
            .select("*") \
            .eq("id", connection_id) \
            .eq("user_id", user.id) \
            .execute()
        
        if not connection_response.data:
            raise HTTPException(status_code=404, detail="Broker connection not found")
        
        connection = connection_response.data[0]
        
        if not connection.get("is_active"):
            raise HTTPException(status_code=400, detail="Broker connection is not active")
        
        portfolio = None
        
        # Fetch portfolio based on broker using new connection modules
        if connection["broker_name"] == "IOL":
            # Decrypt credentials
            username = decrypt_api_key(connection["username_encrypted"])
            password = decrypt_api_key(connection["password_encrypted"])
            
            # Use new IOL connection module
            conexion_iol = ConexionIOL(username, password)
            portfolio = await conexion_iol.obtener_portfolio()
            if portfolio is None:
                raise HTTPException(status_code=400, detail="Failed to fetch portfolio from IOL")
        
        elif connection["broker_name"] == "BINANCE":
            # Decrypt credentials
            api_key = decrypt_api_key(connection["api_key_encrypted"])
            api_secret = decrypt_api_key(connection["api_secret_encrypted"])
            
            # Use new Binance connection module
            conexion_binance = ConexionBinance(api_key, api_secret)
            portfolio = await conexion_binance.obtener_portfolio()
            if portfolio is None:
                raise HTTPException(status_code=400, detail="Failed to fetch portfolio from Binance")
        
        if portfolio is None:
            raise HTTPException(status_code=500, detail="Failed to fetch portfolio from broker")
        
        # Update last_synced timestamp
        supabase.table("broker_connections") \
            .update({"last_synced": datetime.now(timezone.utc).isoformat()}) \
            .eq("id", connection_id) \
            .execute()
        
        return {
            "broker": connection["broker_name"],
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "portfolio": portfolio
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching broker portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching broker portfolio: {str(e)}")

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
# AUTHENTICATION HELPERS (DUPLICADAS - ELIMINADAS)
# ============================================
# Las funciones decode_jwt y ensure_user_persisted están definidas arriba:
# - decode_jwt: línea 368
# - ensure_user_persisted: línea 393 (versión mejorada con reintentos y creación manual)

# Funciones duplicadas eliminadas - usar las versiones de arriba:
# decode_jwt está en línea 368
# ensure_user_persisted está en línea 393 (versión mejorada con reintentos y creación manual)

async def create_default_subscription(user_id: str):
    """Crea una suscripción por defecto con plan free (sin trial automático)"""
    try:
        # Obtener el plan "free" (plan gratuito)
        plan_response = supabase.table("subscription_plans").select("*").eq("name", "free").execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            logger.error("Plan 'free' no encontrado")
            return
        
        plan = plan_response.data[0]
        plan_id = plan["id"]
        
        # Calcular fechas (sin trial, solo plan free)
        now = datetime.now(timezone.utc)
        
        # Crear suscripción sin trial (plan free permanente)
        subscription_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": "active",
            "trial_start": None,
            "trial_end": None,
            "current_period_start": now.isoformat(),
            "current_period_end": None  # Plan free no tiene fecha de fin
        }
        
        subscription_response = supabase.table("subscriptions").insert(subscription_data).execute()
        
        if subscription_response.data:
            logger.info(f"Suscripción free creada para usuario {user_id}")
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
    confirm_password: str
    country: str
    date_of_birth: str  # Format: YYYY-MM-DD

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: Optional[str] = None  # Token puede venir del header o del body
    password: str
    confirm_password: str

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
    """Registro de nuevo usuario con email, password, country y date_of_birth"""
    try:
        # Validar que las contraseñas coincidan
        if signup_data.password != signup_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las contraseñas no coinciden"
            )
        
        # Validar longitud de contraseña
        if len(signup_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 6 caracteres"
            )
        
        # Validar fecha de nacimiento
        try:
            birth_date = datetime.strptime(signup_data.date_of_birth, "%Y-%m-%d")
            # Verificar que sea mayor de 13 años (requisito común)
            age = (datetime.now() - birth_date).days / 365.25
            if age < 13:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debes ser mayor de 13 años para registrarte"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha inválido. Use YYYY-MM-DD"
            )
        
        logger.info(f"Registrando usuario: {signup_data.email}")
        
        # Verificar si el usuario ya existe antes de intentar crear
        try:
            # Intentar iniciar sesión primero para verificar si existe
            existing_user = supabase.auth.sign_in_with_password({
                "email": signup_data.email,
                "password": signup_data.password
            })
            if existing_user.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este email ya está registrado. Por favor, inicia sesión."
                )
        except Exception:
            # Si falla el sign_in, el usuario no existe, continuar con el registro
            pass
        
        # Crear nuevo usuario
        try:
            auth_response = supabase.auth.sign_up({
                "email": signup_data.email,
                "password": signup_data.password,
                "options": {
                    # "email_redirect_to": f"{os.getenv('FRONTEND_URL', 'http://localhost:8080')}/login.html"
                    "email_redirect_to": f"{os.getenv('FRONTEND_URL', 'https://bullanalytics.io')}/login.html"
                }
            })
        except Exception as signup_error:
            error_msg = str(signup_error)
            logger.error(f"Error en sign_up: {error_msg}")
            if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este email ya está registrado. Por favor, inicia sesión."
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear el usuario: {error_msg}"
            )
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear el usuario. Verifica que el email no esté registrado."
            )
        
        user_id = auth_response.user.id
        email = auth_response.user.email
        
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El usuario se creó pero no se pudo obtener el ID o email. Por favor, intenta nuevamente."
            )
        
        logger.info(f"Usuario creado en auth.users: {user_id} ({email})")
        
        # Verificar si el usuario necesita confirmación de email
        # Si no está confirmado, intentar confirmarlo automáticamente para evitar que sea eliminado
        if not auth_response.user.email_confirmed_at:
            logger.warning(f"Usuario {email} creado pero email no confirmado. Intentando confirmar automáticamente...")
            try:
                # Intentar confirmar el email automáticamente usando el token de confirmación
                # Nota: Esto requiere que Supabase esté configurado para permitir auto-confirmación
                # Si no funciona, el usuario deberá confirmar manualmente
                if hasattr(auth_response, 'session') and auth_response.session:
                    logger.info(f"Usuario {email} tiene sesión activa, considerando como confirmado")
                else:
                    logger.warning(f"Usuario {email} no tiene sesión. Puede ser eliminado si no confirma el email.")
            except Exception as confirm_error:
                logger.warning(f"No se pudo confirmar automáticamente el email: {str(confirm_error)}")
        
        # Intentar crear el perfil inmediatamente después de crear el usuario
        # Esto evita problemas de timing donde el usuario puede ser eliminado antes de que el trigger se ejecute
        import asyncio
        await asyncio.sleep(0.5)  # Esperar medio segundo para que el trigger tenga oportunidad
        
        # Verificar si el trigger ya creó el registro
        initial_check = supabase.table(USER_TABLE_NAME).select("*").eq("id", user_id).execute()
        if not initial_check.data or len(initial_check.data) == 0:
            # El trigger no se ejecutó aún, intentar crear el registro manualmente inmediatamente
            logger.info(f"Trigger no ejecutado aún, creando registro manualmente para evitar problemas de timing...")
            try:
                manual_profile = {
                    "id": user_id,
                    "email": email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                manual_insert = supabase.table(USER_TABLE_NAME).insert(manual_profile).execute()
                if manual_insert.data and len(manual_insert.data) > 0:
                    logger.info(f"Perfil creado manualmente exitosamente para {user_id}")
                else:
                    logger.warning(f"Insert manual no devolvió datos, pero continuando...")
            except Exception as manual_error:
                error_msg = str(manual_error)
                # Si es un error de foreign key, el usuario ya no existe - esto es crítico
                if "foreign key" in error_msg.lower() or "23503" in error_msg:
                    logger.error(f"CRÍTICO: Usuario {user_id} no existe en auth.users. El usuario fue eliminado antes de crear el perfil.")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="El usuario se creó pero fue eliminado antes de completar el registro. Esto puede ocurrir si el email no está confirmado. Por favor, verifica tu email o intenta registrarte nuevamente."
                    )
                # Si es un error de conflicto (ya existe), está bien, continuar
                elif "conflict" in error_msg.lower() or "duplicate" in error_msg.lower() or "23505" in error_msg:
                    logger.info(f"El perfil ya existe (probablemente creado por el trigger), continuando...")
                else:
                    logger.warning(f"Error al crear perfil manualmente: {error_msg}, continuando con ensure_user_persisted...")
        
        # Esperar un momento adicional para asegurar que todo esté sincronizado
        await asyncio.sleep(0.5)
        
        # Persistir/actualizar en tabla custom con country y date_of_birth
        # El trigger ya creó el registro básico, ahora lo actualizamos con los datos adicionales
        user_data = await ensure_user_persisted(
            user_id, 
            email, 
            "email_password",
            country=signup_data.country,
            date_of_birth=signup_data.date_of_birth
        )
        
        # Obtener token
        access_token = auth_response.session.access_token if auth_response.session else None
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Usuario creado pero no se pudo obtener el token"
            )
        
        logger.info(f"Usuario {email} registrado exitosamente")
        
        # Crear suscripción gratuita por defecto
        try:
            await create_default_subscription(user_id)
            logger.info(f"Suscripción gratuita creada para usuario {user_id}")
        except Exception as sub_error:
            logger.error(f"Error al crear suscripción gratuita: {str(sub_error)}")
            # No fallar el registro si la suscripción falla, solo loguear el error
        
        # Enviar email de onboarding
        try:
            user_name = email.split("@")[0] if email else "Usuario"
            onboarding_template = get_onboarding_email_template(user_name, email)
            send_alert_email(
                to_email=email,
                subject=onboarding_template["subject"],
                html_content=onboarding_template["html_content"],
                sender_name="BullAnalytics",
                sender_email="noreply@aperturaia.com"
            )
            logger.info(f"Email de onboarding enviado a {email}")
        except Exception as email_error:
            logger.error(f"Error al enviar email de onboarding: {str(email_error)}")
            # No fallar el registro si el email falla, solo loguear el error
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse(
                user_id=user_data["id"],  # user_profiles usa 'id' como PK
                email=user_data["email"],
                auth_source=user_data.get("auth_source", "email_password"),
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
                auth_source=user_data.get("auth_source", "email_password"),
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

# OAuth endpoints removed - using traditional email/password registration only

@app.post("/auth/forgot-password", tags=["Authentication"])
async def forgot_password(request: ForgotPasswordRequest):
    """Solicitar recuperación de contraseña"""
    try:
        logger.info(f"Solicitando recuperación de contraseña para: {request.email}")
        
        # Enviar email de recuperación usando Supabase Auth
        try:
            supabase.auth.reset_password_for_email(
                request.email,
                {
                    # "redirect_to": f"{os.getenv('FRONTEND_URL', 'http://localhost:8080')}/reset-password.html"
                    "redirect_to": f"{os.getenv('FRONTEND_URL', 'https://bullanalytics.io')}/reset-password.html"
                }
            )
            logger.info(f"Email de recuperación enviado a {request.email}")
        except Exception as email_error:
            logger.warning(f"Error enviando email de recuperación: {str(email_error)}")
            # Continuar de todas formas para no revelar si el email existe
        
        # Siempre retornar éxito (por seguridad, no revelar si el email existe)
        return {
            "message": "Si el email existe, recibirás un enlace para recuperar tu contraseña"
        }
        
    except Exception as e:
        logger.error(f"Error en forgot_password: {str(e)}")
        # Retornar éxito incluso si hay error (por seguridad)
        return {
            "message": "Si el email existe, recibirás un enlace para recuperar tu contraseña"
        }

@app.post("/auth/reset-password", tags=["Authentication"])
async def reset_password(request: ResetPasswordRequest, authorization: Optional[str] = Header(None)):
    """Restablecer contraseña con token"""
    try:
        # Validar que las contraseñas coincidan
        if request.password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las contraseñas no coinciden"
            )
        
        # Validar longitud de contraseña
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 6 caracteres"
            )
        
        # Obtener token del header o del body
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        elif request.token:
            token = request.token
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de recuperación requerido"
            )
        
        logger.info("Restableciendo contraseña")
        
        # En Supabase, cuando el usuario hace clic en el enlace del email de recuperación,
        # Supabase redirige a la URL con un hash que contiene el token de recuperación.
        # El token de recuperación debe ser usado con exchange_code_for_session para establecer
        # una sesión temporal, y luego podemos actualizar la contraseña.
        
        try:
            # El token de recuperación viene en el hash de la URL cuando el usuario hace clic
            # en el enlace del email. Necesitamos usar exchange_code_for_session para convertir
            # el token de recuperación en una sesión temporal.
            
            # En Supabase, cuando el usuario hace clic en el enlace del email de recuperación,
            # el token viene en el hash de la URL. Este token es un token de recuperación que
            # puede ser usado con verify_otp para establecer una sesión temporal.
            
            # En Supabase, cuando el usuario hace clic en el enlace del email de recuperación,
            # Supabase redirige con un hash que contiene el access_token y refresh_token.
            # Para el flujo PKCE, el token viene como token_hash en los query parameters.
            # Necesitamos manejar ambos casos.
            
            # En Supabase, cuando el usuario hace clic en el enlace del email de recuperación,
            # Supabase redirige con un hash que contiene el access_token y refresh_token.
            # Para el flujo PKCE, el token viene como token_hash en los query parameters.
            # Intentar primero con set_session (más común en flujo implícito) y luego con verify_otp (PKCE)
            
            try:
                # Intentar primero establecer la sesión directamente con el token
                # (esto funciona si el token es un access_token del hash en el flujo implícito)
                session_result = supabase.auth.set_session(token, token)
                
                # Verificar que la sesión se estableció correctamente
                current_user_response = supabase.auth.get_user()
                if not current_user_response.user:
                    raise Exception("No se pudo establecer la sesión")
                
                # Ahora intentar actualizar la contraseña
                result = supabase.auth.update_user({
                    "password": request.password
                })
                
                if not result.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No se pudo actualizar la contraseña. Por favor, intenta de nuevo."
                    )
                
                logger.info(f"Contraseña restablecida exitosamente (método set_session) para usuario {result.user.id}")
                
            except Exception as session_error:
                logger.warning(f"Error en set_session: {str(session_error)}")
                # Si set_session falla, intentar con verify_otp (flujo PKCE)
                try:
                    # Intentar con token_hash (flujo PKCE)
                    verify_response = supabase.auth.verify_otp({
                        "token_hash": token,
                        "type": "recovery"
                    })
                    
                    if not hasattr(verify_response, 'session') or not verify_response.session:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Token inválido o expirado. Por favor, solicita un nuevo enlace de recuperación."
                        )
                    
                    # Ahora que tenemos la sesión, podemos actualizar la contraseña
                    result = supabase.auth.update_user({
                        "password": request.password
                    })
                    
                    if not result.user:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No se pudo actualizar la contraseña. Por favor, intenta de nuevo."
                        )
                    
                    logger.info(f"Contraseña restablecida exitosamente (método verify_otp) para usuario {result.user.id}")
                    
                except Exception as verify_error:
                    error_msg = str(verify_error)
                    logger.error(f"Error en verify_otp: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Token inválido o expirado. Por favor, solicita un nuevo enlace de recuperación."
                    )
            
        except HTTPException:
            raise
        
        return {
            "message": "Contraseña restablecida exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en reset_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al restablecer contraseña: {str(e)}"
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
    """Obtiene la suscripción actual del usuario. Si no existe, crea una suscripción gratuita por defecto."""
    try:
        response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            # No hay suscripción activa, crear una suscripción gratuita por defecto
            logger.info(f"Usuario {user.id} no tiene suscripción activa, creando suscripción gratuita por defecto...")
            try:
                await create_default_subscription(user.id)
                # Intentar obtener la suscripción nuevamente
                response = supabase.table("subscriptions") \
                    .select("*, subscription_plans(*)") \
                    .eq("user_id", user.id) \
                    .eq("status", "active") \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                
                if not response.data or len(response.data) == 0:
                    raise HTTPException(status_code=404, detail="No se pudo crear la suscripción por defecto")
            except Exception as create_error:
                logger.error(f"Error al crear suscripción por defecto: {str(create_error)}")
                raise HTTPException(status_code=404, detail="No active subscription found and could not create default subscription")
        
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

class StartTrialRequest(BaseModel):
    plan_name: str  # "plus" o "pro"

@app.post("/api/subscriptions/start-trial", tags=["Subscriptions"])
async def start_trial(
    request: StartTrialRequest,
    user = Depends(get_current_user)
):
    """Iniciar un trial gratuito para un plan (7 días Plus, 3 días Pro)"""
    try:
        user_id = user.id
        
        # Validar que el plan sea válido para trial
        valid_trial_plans = {
            "plus": 7,  # 7 días de trial
            "pro": 3    # 3 días de trial
        }
        
        plan_name = request.plan_name.lower()
        if plan_name not in valid_trial_plans:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El plan '{plan_name}' no tiene trial disponible. Solo 'plus' (7 días) y 'pro' (3 días) tienen trials."
            )
        
        trial_days = valid_trial_plans[plan_name]
        
        # Verificar si el usuario ya tiene una suscripción activa
        subscription_response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user_id) \
            .eq("status", "active") \
            .execute()
        
        current_subscription = subscription_response.data[0] if subscription_response.data else None
        
        # Si ya tiene un trial activo o una suscripción pagada, no permitir otro trial
        if current_subscription:
            current_plan_name = current_subscription.get("subscription_plans", {}).get("name") if isinstance(current_subscription.get("subscription_plans"), dict) else None
            if not current_plan_name:
                # Intentar obtener el plan_name de otra forma
                plan_response = supabase.table("subscription_plans") \
                    .select("name") \
                    .eq("id", current_subscription.get("plan_id")) \
                    .execute()
                if plan_response.data:
                    current_plan_name = plan_response.data[0].get("name")
            
            # Verificar si ya tiene un trial activo
            trial_end = current_subscription.get("trial_end")
            if trial_end:
                trial_end_date = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                if trial_end_date > datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ya tienes un trial activo. Espera a que termine antes de iniciar otro."
                    )
            
            # Si ya tiene el plan que quiere hacer trial, no permitir
            if current_plan_name == plan_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya tienes el plan {plan_name}. No puedes iniciar un trial para un plan que ya tienes."
                )
        
        # Obtener el plan solicitado
        plan_response = supabase.table("subscription_plans") \
            .select("*") \
            .eq("name", plan_name) \
            .execute()
        
        if not plan_response.data or len(plan_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan '{plan_name}' no encontrado"
            )
        
        plan = plan_response.data[0]
        plan_id = plan["id"]
        
        # Calcular fechas del trial
        now = datetime.utcnow()
        trial_end = now + timedelta(days=trial_days)
        
        # Si ya tiene una suscripción, actualizarla; si no, crear una nueva
        if current_subscription:
            # Actualizar suscripción existente
            update_data = {
                "plan_id": plan_id,
                "status": "active",
                "trial_start": now.isoformat(),
                "trial_end": trial_end.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": trial_end.isoformat()
            }
            
            update_response = supabase.table("subscriptions") \
                .update(update_data) \
                .eq("id", current_subscription["id"]) \
                .execute()
            
            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al actualizar la suscripción"
                )
            
            logger.info(f"Trial de {trial_days} días iniciado para usuario {user_id} con plan {plan_name}")
            
            return {
                "message": f"Trial de {trial_days} días iniciado exitosamente",
                "trial_end": trial_end.isoformat(),
                "days_remaining": trial_days
            }
        else:
            # Crear nueva suscripción con trial
            subscription_data = {
                "user_id": user_id,
                "plan_id": plan_id,
                "status": "active",
                "trial_start": now.isoformat(),
                "trial_end": trial_end.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": trial_end.isoformat()
            }
            
            insert_response = supabase.table("subscriptions").insert(subscription_data).execute()
            
            if not insert_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al crear la suscripción con trial"
                )
            
            logger.info(f"Trial de {trial_days} días iniciado para usuario {user_id} con plan {plan_name}")
            
            return {
                "message": f"Trial de {trial_days} días iniciado exitosamente",
                "trial_end": trial_end.isoformat(),
                "days_remaining": trial_days
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error iniciando trial: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar trial: {str(e)}"
        )

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
    """Obtiene la suscripción actual del usuario. Si no existe, crea una suscripción gratuita por defecto."""
    try:
        response = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if not response.data or len(response.data) == 0:
            # No hay suscripción activa, crear una suscripción gratuita por defecto
            logger.info(f"Usuario {user.id} no tiene suscripción activa, creando suscripción gratuita por defecto...")
            try:
                await create_default_subscription(user.id)
                # Intentar obtener la suscripción nuevamente
                response = supabase.table("subscriptions") \
                    .select("*, subscription_plans(*)") \
                    .eq("user_id", user.id) \
                    .eq("status", "active") \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                
                if not response.data or len(response.data) == 0:
                    raise HTTPException(status_code=404, detail="No se pudo crear la suscripción por defecto")
            except Exception as create_error:
                logger.error(f"Error al crear suscripción por defecto: {str(create_error)}")
                raise HTTPException(status_code=404, detail="No active subscription found and could not create default subscription")
        
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
        coupon_code = coupon.code.strip().upper()
        
        # Get plan_id
        plan_response = supabase.table("subscription_plans") \
            .select("id") \
            .eq("name", coupon.plan_name) \
            .single() \
            .execute()
        
        if not plan_response.data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan_id = plan_response.data["id"]
        
        # Buscar cupón
        coupon_response = supabase.table("coupons") \
            .select("*") \
            .eq("code", coupon_code) \
            .eq("is_active", True) \
            .execute()
        
        if not coupon_response.data or len(coupon_response.data) == 0:
            return {
                "valid": False,
                "message": "Código de cupón inválido o inactivo"
            }
        
        coupon_data = coupon_response.data[0]
        
        # Verificar que el cupón es para el plan correcto
        if coupon_data.get("plan_id") and coupon_data["plan_id"] != plan_id:
            return {
                "valid": False,
                "message": "Este cupón no es válido para el plan seleccionado"
            }
        
        # Verificar límite de redenciones
        if coupon_data.get("max_redemptions"):
            times_redeemed = coupon_data.get("times_redeemed", 0)
            if times_redeemed >= coupon_data["max_redemptions"]:
                return {
                    "valid": False,
                    "message": "Este cupón ha alcanzado su límite de usos"
                }
        
        # Verificar si el usuario ya usó este cupón
        existing_redemption = supabase.table("coupon_redemptions") \
            .select("*") \
            .eq("coupon_id", coupon_data["id"]) \
            .eq("user_id", user.id) \
            .execute()
        
        if existing_redemption.data and len(existing_redemption.data) > 0:
            return {
                "valid": False,
                "message": "Ya has usado este cupón anteriormente"
            }
        
        # Verificar fechas de validez
        # Usar datetime con timezone para evitar errores de comparación
        now = datetime.now(timezone.utc)
        if coupon_data.get("valid_from"):
            valid_from_str = coupon_data["valid_from"]
            if isinstance(valid_from_str, str):
                # Si tiene Z, reemplazarlo con +00:00 para timezone UTC
                if valid_from_str.endswith("Z"):
                    valid_from_str = valid_from_str.replace("Z", "+00:00")
                valid_from = datetime.fromisoformat(valid_from_str)
                # Si no tiene timezone, asumir UTC
                if valid_from.tzinfo is None:
                    valid_from = valid_from.replace(tzinfo=timezone.utc)
            else:
                # Si es un datetime object, asegurar que tenga timezone
                valid_from = valid_from_str
                if valid_from.tzinfo is None:
                    valid_from = valid_from.replace(tzinfo=timezone.utc)
            
            if now < valid_from:
                return {
                    "valid": False,
                    "message": "Este cupón aún no es válido"
                }
        
        if coupon_data.get("valid_until"):
            valid_until_str = coupon_data["valid_until"]
            if isinstance(valid_until_str, str):
                # Si tiene Z, reemplazarlo con +00:00 para timezone UTC
                if valid_until_str.endswith("Z"):
                    valid_until_str = valid_until_str.replace("Z", "+00:00")
                valid_until = datetime.fromisoformat(valid_until_str)
                # Si no tiene timezone, asumir UTC
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
            else:
                # Si es un datetime object, asegurar que tenga timezone
                valid_until = valid_until_str
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
            
            if now > valid_until:
                return {
                    "valid": False,
                    "message": "Este cupón ha expirado"
                }
        
        # Cupón válido
        return {
            "valid": True,
            "coupon": {
                "code": coupon_data["code"],
                "type": coupon_data.get("coupon_type"),
                "discount_percent": coupon_data.get("discount_percent"),
                "discount_amount": coupon_data.get("discount_amount"),
                "duration_months": coupon_data.get("duration_months"),
                "description": coupon_data.get("description")
            },
            "message": "Cupón válido"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating coupon: {str(e)}", exc_info=True)
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

@app.get("/calendar.html")
async def calendar():
    return FileResponse("calendar.html")

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

@app.get("/forgot-password.html")
async def forgot_password_page():
    return FileResponse("forgot-password.html")

@app.get("/reset-password.html")
async def reset_password_page():
    return FileResponse("reset-password.html")

@app.get("/blog.html")
async def blog():
    return FileResponse("blog.html")

@app.get("/calculadora.html")
async def calculadora():
    return FileResponse("calculadora.html")

@app.get("/robots.txt")
async def robots_txt():
    return FileResponse("robots.txt", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap_xml():
    return FileResponse("sitemap.xml", media_type="application/xml")

@app.get("/docs/LEGAL.md")
async def serve_legal_md():
    """Serve legal markdown file"""
    return FileResponse("docs/LEGAL.md", media_type="text/markdown")

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
            <!-- <a href="http://localhost:8080/rules.html" class="button">Gestionar Alertas</a> -->
            <a href="https://bullanalytics.io/rules.html" class="button">Gestionar Alertas</a>
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
    coupon_code: Optional[str] = None  # Código de cupón opcional

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
        plan_id = plan["id"]
        paypal_plan_id = plan.get("paypal_plan_id")
        
        if not paypal_plan_id:
            raise HTTPException(
                status_code=400,
                detail=f"Plan '{request.plan_name}' no tiene paypal_plan_id configurado. Configúralo en Supabase."
            )
        
        # 2. Validar y aplicar cupón si se proporciona
        coupon_id = None
        coupon_data = None
        if request.coupon_code:
            coupon_code = request.coupon_code.strip().upper()
            logger.info(f"Validando cupón: {coupon_code} para plan: {request.plan_name}")
            
            # Buscar cupón
            coupon_response = supabase.table("coupons") \
                .select("*") \
                .eq("code", coupon_code) \
                .eq("is_active", True) \
                .execute()
            
            if not coupon_response.data or len(coupon_response.data) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Código de cupón inválido o inactivo"
                )
            
            coupon_data = coupon_response.data[0]
            
            # Verificar que el cupón es para el plan correcto
            if coupon_data.get("plan_id") and coupon_data["plan_id"] != plan_id:
                raise HTTPException(
                    status_code=400,
                    detail="Este cupón no es válido para el plan seleccionado"
                )
            
            # Verificar límite de redenciones
            if coupon_data.get("max_redemptions"):
                times_redeemed = coupon_data.get("times_redeemed", 0)
                if times_redeemed >= coupon_data["max_redemptions"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Este cupón ha alcanzado su límite de usos"
                    )
            
            # Verificar si el usuario ya usó este cupón
            existing_redemption = supabase.table("coupon_redemptions") \
                .select("*") \
                .eq("coupon_id", coupon_data["id"]) \
                .eq("user_id", user.id) \
                .execute()
            
            if existing_redemption.data and len(existing_redemption.data) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Ya has usado este cupón anteriormente"
                )
            
            # Verificar fechas de validez
            # Usar datetime con timezone para evitar errores de comparación
            now = datetime.now(timezone.utc)
            if coupon_data.get("valid_from"):
                valid_from_str = coupon_data["valid_from"]
                if isinstance(valid_from_str, str):
                    # Si tiene Z, reemplazarlo con +00:00 para timezone UTC
                    if valid_from_str.endswith("Z"):
                        valid_from_str = valid_from_str.replace("Z", "+00:00")
                    valid_from = datetime.fromisoformat(valid_from_str)
                    # Si no tiene timezone, asumir UTC
                    if valid_from.tzinfo is None:
                        valid_from = valid_from.replace(tzinfo=timezone.utc)
                else:
                    # Si es un datetime object, asegurar que tenga timezone
                    valid_from = valid_from_str
                    if valid_from.tzinfo is None:
                        valid_from = valid_from.replace(tzinfo=timezone.utc)
                
                if now < valid_from:
                    raise HTTPException(
                        status_code=400,
                        detail="Este cupón aún no es válido"
                    )
            
            if coupon_data.get("valid_until"):
                valid_until_str = coupon_data["valid_until"]
                if isinstance(valid_until_str, str):
                    # Si tiene Z, reemplazarlo con +00:00 para timezone UTC
                    if valid_until_str.endswith("Z"):
                        valid_until_str = valid_until_str.replace("Z", "+00:00")
                    valid_until = datetime.fromisoformat(valid_until_str)
                    # Si no tiene timezone, asumir UTC
                    if valid_until.tzinfo is None:
                        valid_until = valid_until.replace(tzinfo=timezone.utc)
                else:
                    # Si es un datetime object, asegurar que tenga timezone
                    valid_until = valid_until_str
                    if valid_until.tzinfo is None:
                        valid_until = valid_until.replace(tzinfo=timezone.utc)
                
                if now > valid_until:
                    raise HTTPException(
                        status_code=400,
                        detail="Este cupón ha expirado"
                    )
            
            coupon_id = coupon_data["id"]
            logger.info(f"Cupón válido: {coupon_code}, tipo: {coupon_data.get('coupon_type')}")
        
        # 3. Verificar si el usuario ya tiene una suscripción activa
        existing_sub = supabase.table("subscriptions") \
            .select("*, subscription_plans(*)") \
            .eq("user_id", user.id) \
            .in_("status", ["active", "pending_approval"]) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        # Si tiene una suscripción activa, verificar si es un upgrade/downgrade
        if existing_sub.data and len(existing_sub.data) > 0:
            current_subscription = existing_sub.data[0]
            current_plan_id = current_subscription.get("plan_id")
            current_plan_name = current_subscription.get("subscription_plans", {}).get("name") if isinstance(current_subscription.get("subscription_plans"), dict) else None
            
            # Si el plan es el mismo, rechazar
            if current_plan_id == plan_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya tienes una suscripción activa con el plan '{request.plan_name}'. Selecciona un plan diferente."
                )
            
            # Es un upgrade/downgrade - cancelar la suscripción actual en PayPal
            paypal_sub_id = current_subscription.get("paypal_subscription_id")
            if paypal_sub_id:
                logger.info(f"Usuario {user.id} tiene suscripción activa ({current_plan_name}). Cancelando para upgrade a {request.plan_name}...")
                try:
                    access_token_cancel = get_paypal_access_token()
                    cancel_headers = {
                        "Authorization": f"Bearer {access_token_cancel}",
                        "Content-Type": "application/json"
                    }
                    cancel_payload = {
                        "reason": f"Upgrade de {current_plan_name} a {request.plan_name}"
                    }
                    
                    cancel_response = requests.post(
                        f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{paypal_sub_id}/cancel",
                        headers=cancel_headers,
                        json=cancel_payload
                    )
                    
                    if cancel_response.status_code in [204, 200]:
                        logger.info(f"Suscripción {paypal_sub_id} cancelada exitosamente para upgrade")
                        # Actualizar estado en Supabase
                        supabase.table("subscriptions") \
                            .update({
                                "status": "canceled",
                                "canceled_at": datetime.now(timezone.utc).isoformat()
                            }) \
                            .eq("id", current_subscription["id"]) \
                            .execute()
                    else:
                        logger.warning(f"No se pudo cancelar suscripción en PayPal: {cancel_response.status_code} - {cancel_response.text}")
                        # Continuar de todas formas para crear la nueva suscripción
                except Exception as cancel_error:
                    logger.error(f"Error cancelando suscripción anterior: {str(cancel_error)}")
                    # Continuar de todas formas para crear la nueva suscripción
            else:
                # No tiene paypal_subscription_id, solo actualizar estado en Supabase
                logger.info(f"Usuario {user.id} tiene suscripción sin PayPal ID. Actualizando estado...")
                supabase.table("subscriptions") \
                    .update({
                        "status": "canceled",
                        "canceled_at": datetime.now(timezone.utc).isoformat()
                    }) \
                    .eq("id", current_subscription["id"]) \
                    .execute()
        
        # 4. Obtener email del usuario
        user_profile = supabase.table("user_profiles") \
            .select("email") \
            .eq("id", user.id) \
            .single() \
            .execute()
        
        user_email = user_profile.data.get("email") if user_profile.data else user.id
        
        # 5. Verificar si es un cupón de tipo "free_access" - en ese caso, NO usar PayPal
        if coupon_data and coupon_data.get("coupon_type") == "free_access":
            logger.info(f"Cupón de tipo free_access detectado. Creando suscripción directamente sin PayPal...")
            
            # Calcular período de suscripción basado en duration_months del cupón
            now = datetime.now(timezone.utc)
            duration_months = coupon_data.get("duration_months", 12)
            period_end = now + timedelta(days=duration_months * 30)
            
            # Crear suscripción directamente en Supabase (sin PayPal)
            subscription_record = {
                "user_id": user.id,
                "plan_id": plan["id"],
                "status": "active",  # Activa inmediatamente
                "paypal_subscription_id": None,  # Sin PayPal
                "current_period_start": now.isoformat(),
                "current_period_end": period_end.isoformat(),
                "coupon_id": coupon_id,
                "trial_start": now.isoformat(),
                "trial_end": period_end.isoformat()
            }
            
            supabase_response = supabase.table("subscriptions").insert(subscription_record).execute()
            
            if not supabase_response.data:
                logger.error("No se pudo guardar la suscripción gratuita en Supabase")
                raise HTTPException(status_code=500, detail="Error guardando suscripción en base de datos")
            
            subscription_db_id = supabase_response.data[0]["id"]
            
            # Registrar el uso del cupón
            supabase.table("coupons") \
                .update({"times_redeemed": coupon_data.get("times_redeemed", 0) + 1}) \
                .eq("id", coupon_id) \
                .execute()
            
            supabase.table("coupon_redemptions") \
                .insert({
                    "coupon_id": coupon_id,
                    "user_id": user.id,
                    "subscription_id": subscription_db_id
                }) \
                .execute()
            
            logger.info(f"✅ Suscripción gratuita creada exitosamente para usuario {user.id} con cupón {request.coupon_code}")
            
            # Retornar éxito sin approval_url (no hay PayPal)
            return {
                "success": True,
                "subscription_id": subscription_db_id,
                "skip_paypal": True,  # Indicador para el frontend
                "message": f"¡Suscripción activada! Tu plan {request.plan_name.upper()} está activo por {duration_months} meses gracias al cupón.",
                "plan_name": request.plan_name,
                "duration_months": duration_months,
                "period_end": period_end.isoformat()
            }
        
        # 5b. Para otros tipos de cupón o sin cupón, continuar con PayPal
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
        
        # 6. Guardar referencia en Supabase (status='pending_approval' hasta aprobación)
        # Calcular fechas por defecto (se actualizarán con webhook cuando se active)
        now = datetime.now(timezone.utc)
        # Período normal según el plan (mensual o anual)
        billing_interval = plan.get("billing_interval", "month")
        if billing_interval == "year":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        subscription_record = {
            "user_id": user.id,
            "plan_id": plan["id"],
            "status": "pending_approval",
            "paypal_subscription_id": paypal_subscription_id,
            "current_period_start": now.isoformat(),  # Fecha actual como valor temporal
            "current_period_end": period_end.isoformat(),  # Se actualizará con webhook cuando se active
            "coupon_id": coupon_id  # Guardar referencia al cupón si existe
        }
        
        supabase_response = supabase.table("subscriptions").insert(subscription_record).execute()
        
        if not supabase_response.data:
            logger.error("No se pudo guardar la suscripción en Supabase")
            raise HTTPException(status_code=500, detail="Error guardando suscripción en base de datos")
        
        subscription_db_id = supabase_response.data[0]["id"]
        
        # 7. Registrar el uso del cupón si se aplicó (para cupones no-free_access)
        if coupon_id and coupon_data:
            # Incrementar times_redeemed
            supabase.table("coupons") \
                .update({"times_redeemed": coupon_data.get("times_redeemed", 0) + 1}) \
                .eq("id", coupon_id) \
                .execute()
            
            # Registrar en coupon_redemptions
            supabase.table("coupon_redemptions") \
                .insert({
                    "coupon_id": coupon_id,
                    "user_id": user.id,
                    "subscription_id": subscription_db_id
                }) \
                .execute()
            
            logger.info(f"Cupón {request.coupon_code} aplicado y registrado para usuario {user.id}")
        
        # 8. Obtener approval_url
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
                        update_data["current_period_start"] = datetime.now(timezone.utc).isoformat()
                        # Calcular end basado en el plan
                        plan_response = supabase.table("subscription_plans") \
                            .select("billing_interval") \
                            .eq("id", subscription["plan_id"]) \
                            .single() \
                            .execute()
                        
                        if plan_response.data:
                            interval = plan_response.data.get("billing_interval", "month")
                            if interval == "month":
                                update_data["current_period_end"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                            elif interval == "year":
                                update_data["current_period_end"] = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
            
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

@app.post("/api/webhooks/vexor")
async def vexor_webhook(request: Request):
    """
    Recibe notificaciones de Vexor para actualizar el estado de las suscripciones
    Compatible con PayPal y Mercado Pago a través de Vexor.
    """
    try:
        payload = await request.json()
        logger.info(f"🔔 Webhook de Vexor recibido: {payload}")
        
        # Extraer información básica
        # Vexor envía el identificador único de la operación
        vexor_id = payload.get("identifier")
        event_type = payload.get("event")  # Ej: 'subscription.created', 'payment.succeeded'
        platform = payload.get("platform") # 'paypal' o 'mercadopago'
        
        # Recuperar los metadatos que enviamos desde la Edge Function
        custom_data = payload.get("customData", {})
        user_id = custom_data.get("user_id")
        plan_id = custom_data.get("plan_id")
        
        if not user_id or not plan_id:
            logger.warning(f"⚠️ Webhook de Vexor {vexor_id} ignorado: falta user_id o plan_id en customData")
            return {"status": "ignored", "reason": "missing_metadata"}

        # Mapear el estado según el evento
        # Vexor normaliza los eventos de diferentes plataformas
        new_status = "active"
        if event_type in ["subscription.cancelled", "subscription.expired", "payment.failed"]:
            new_status = "inactive"
        elif event_type == "subscription.past_due":
            new_status = "past_due"

        # Datos para actualizar/insertar en Supabase
        now = datetime.now(timezone.utc)
        update_data = {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": new_status,
            "vexor_id": vexor_id,
            "platform": platform,
            "updated_at": now.isoformat()
        }

        # Si es un evento de éxito, actualizamos el periodo de vigencia
        if new_status == "active":
            update_data["current_period_start"] = now.isoformat()
            # Por defecto sumamos 30 días, el webhook de renovación actualizará esto luego
            update_data["current_period_end"] = (now + timedelta(days=32)).isoformat()

        # 1. Buscar si ya existe la suscripción en nuestra tabla
        # Intentamos buscar por vexor_id
        check_response = supabase.table("subscriptions").select("*").eq("vexor_id", vexor_id).execute()
        
        if check_response.data and len(check_response.data) > 0:
            # Actualizar existente
            supabase.table("subscriptions").update(update_data).eq("vexor_id", vexor_id).execute()
            logger.info(f"✅ Suscripción Vexor {vexor_id} actualizada para usuario {user_id} (Estado: {new_status})")
        else:
            # 2. Si no existe por vexor_id, quizás existe una pendiente del usuario para ese plan
            # Esto ayuda a limpiar registros temporales si los hubiera
            user_check = supabase.table("subscriptions") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("status", "pending_approval") \
                .execute()
                
            if user_check.data and len(user_check.data) > 0:
                # Reutilizar el registro pendiente
                supabase.table("subscriptions").update(update_data).eq("id", user_check.data[0]["id"]).execute()
                logger.info(f"✅ Registro pendiente convertido a Vexor {vexor_id} para usuario {user_id}")
            else:
                # Crear nuevo registro
                supabase.table("subscriptions").insert(update_data).execute()
                logger.info(f"✅ Nueva suscripción Vexor {vexor_id} creada para usuario {user_id}")

        return {"status": "success", "event": event_type}

    except Exception as e:
        logger.error(f"❌ Error procesando webhook de Vexor: {str(e)}", exc_info=True)
        # Retornamos 200 para que Vexor no reintente infinitamente si es un error de lógica nuestro,
        # pero podrías retornar 500 si quieres reintentos.
        return {"status": "error", "message": str(e)}

# Run server
if __name__ == "__main__":
    print("🚀 Starting BullAnalytics API Server with Supabase...")
    print(f"📊 Supabase URL: {SUPABASE_URL}")
    # print("📡 Server: http://localhost:8080")
    print("📡 Server: https://api.bullanalytics.io")
    print("⚙️  Workers: 4 | Timeout: 120s")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080,
        workers=4,  # Múltiples workers para manejar concurrencia
        timeout_keep_alive=120,  # Timeout más largo
        limit_concurrency=100  # Límite de conexiones concurrentes
    )
