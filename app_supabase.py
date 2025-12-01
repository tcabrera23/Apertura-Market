"""
BullAnalytics API with Supabase Integration
FastAPI backend for financial asset tracking with Supabase PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
from cachetools import TTLCache
import uvicorn
import io
import base64
import json
import os
import re
from groq import Groq
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pwumamzbicapuiqkwrey.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
        
        # Verify token with Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        return user_response.user
    except Exception as e:
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
# RULES ENDPOINTS (Supabase Integration)
# ============================================

@app.get("/api/rules")
async def get_rules(user = Depends(get_current_user)):
    """Get all rules for authenticated user"""
    try:
        response = supabase.table("rules") \
            .select("*") \
            .eq("user_id", user.id) \
            .order("created_at", desc=True) \
            .execute()
        
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

@app.post("/api/rules")
async def create_rule(rule: RuleCreate, user = Depends(get_current_user)):
    """Create a new rule"""
    try:
        # Check user's plan limits
        check_result = supabase.rpc("check_user_plan_limit", {
            "p_user_id": user.id,
            "p_limit_type": "max_rules"
        }).execute()
        
        if not check_result.data:
            raise HTTPException(
                status_code=403,
                detail="Has alcanzado el límite de reglas de tu plan. Actualiza tu suscripción."
            )
        
        rule_data = {
            "user_id": user.id,
            "name": rule.name,
            "rule_type": rule.rule_type,
            "ticker": rule.ticker,
            "value_threshold": rule.value,
            "email": rule.email,
            "is_active": True
        }
        
        response = supabase.table("rules").insert(rule_data).execute()
        
        return {
            "message": "Rule created successfully",
            "rule": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
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

# Run server
if __name__ == "__main__":
    print("🚀 Starting BullAnalytics API Server with Supabase...")
    print(f"📊 Supabase URL: {SUPABASE_URL}")
    print("📡 Server: http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
