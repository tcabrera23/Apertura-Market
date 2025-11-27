from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
from cachetools import TTLCache
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Apertura Finance API",
    description="API for financial asset tracking powered by Yahoo Finance",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache with 2-minute TTL (120 seconds) - Increased size for better performance
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

# Custom watchlists storage
import json
import os

WATCHLISTS_FILE = "watchlists.json"

def load_watchlists():
    """Load custom watchlists from JSON file"""
    if os.path.exists(WATCHLISTS_FILE):
        try:
            with open(WATCHLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_watchlists(watchlists):
    """Save custom watchlists to JSON file"""
    with open(WATCHLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(watchlists, f, indent=2, ensure_ascii=False)

# Response models
class AssetData(BaseModel):
    name: str
    ticker: str
    price: float
    pe_ratio: Optional[float]
    all_time_high: float
    diff_from_max: float

# Helper functions
def get_asset_data(ticker: str, name: str) -> Optional[AssetData]:
    """
    Fetch asset data from Yahoo Finance with caching.
    Cache key includes ticker and current 2-minute window.
    """
    # Create cache key with 2-minute window
    cache_window = int(datetime.now().timestamp() // 120)
    cache_key = f"{ticker}_{cache_window}"
    
    # Check cache first
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="max")
        
        if hist.empty:
            return None
        
        all_time_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        diff_from_max = (current_price - all_time_high) / all_time_high
        pe_ratio = info.get('trailingPE')
        
        asset_data = AssetData(
            name=f"{name} ({ticker})",
            ticker=ticker,
            price=float(current_price),
            pe_ratio=float(pe_ratio) if pe_ratio else None,
            all_time_high=float(all_time_high),
            diff_from_max=float(diff_from_max)
        )
        
        # Store in cache
        cache[cache_key] = asset_data
        
        return asset_data
        
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# API Endpoints
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

@app.get("/api/watchlists")
async def get_watchlists():
    """Get all custom watchlists"""
    return load_watchlists()

@app.get("/api/watchlist/{name}", response_model=List[AssetData])
async def get_watchlist(name: str):
    """Get specific watchlist assets data"""
    watchlists = load_watchlists()
    
    if name not in watchlists:
        raise HTTPException(status_code=404, detail=f"Watchlist '{name}' not found")
    
    results = []
    for ticker, asset_name in watchlists[name].items():
        asset_data = get_asset_data(ticker, asset_name)
        if asset_data:
            results.append(asset_data)
    
    return results

@app.post("/api/watchlist")
async def create_watchlist(name: str, assets: Dict[str, str]):
    """Create or update a custom watchlist"""
    watchlists = load_watchlists()
    watchlists[name] = assets
    save_watchlists(watchlists)
    return {"message": f"Watchlist '{name}' created successfully", "name": name}

@app.delete("/api/watchlist/{name}")
async def delete_watchlist(name: str):
    """Delete a custom watchlist"""
    watchlists = load_watchlists()
    
    if name not in watchlists:
        raise HTTPException(status_code=404, detail=f"Watchlist '{name}' not found")
    
    del watchlists[name]
    save_watchlists(watchlists)
    return {"message": f"Watchlist '{name}' deleted successfully"}

@app.get("/api/asset/{ticker}", response_model=AssetData)
async def get_asset(ticker: str):
    """Get specific asset data"""
    # Check if ticker exists in any list
    name = (TRACKING_ASSETS.get(ticker) or 
            PORTFOLIO_ASSETS.get(ticker) or 
            CRYPTO_ASSETS.get(ticker) or 
            ARGENTINA_ASSETS.get(ticker))
    
    if not name:
        raise HTTPException(status_code=404, detail=f"Asset {ticker} not found")
    
    asset_data = get_asset_data(ticker, name)
    
    if not asset_data:
        raise HTTPException(status_code=500, detail=f"Error fetching data for {ticker}")
    
    return asset_data

# News endpoint
@app.get("/api/news")
async def get_news():
    """Get financial news from Yahoo Finance RSS"""
    import feedparser
    
    # Cache key for news
    cache_key = f"news_{int(datetime.now().timestamp() // 1800)}"  # 30 min cache
    
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # Yahoo Finance RSS feed
        feed_url = "https://finance.yahoo.com/news/rssindex"
        feed = feedparser.parse(feed_url)
        
        news_items = []
        for entry in feed.entries[:20]:  # Get top 20 news
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get('published', ''),
                "summary": entry.get('summary', '')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', '')
            })
        
        cache[cache_key] = news_items
        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

# Rules endpoints
RULES_FILE = "rules.json"

def load_rules():
    """Load rules from JSON file"""
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_rules(rules):
    """Save rules to JSON file"""
    with open(RULES_FILE, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)

@app.get("/api/rules")
async def get_rules():
    """Get all notification rules"""
    return load_rules()

@app.post("/api/rules")
async def create_rule(rule: dict):
    """Create a new notification rule"""
    rules = load_rules()
    rule['id'] = len(rules) + 1
    rule['created_at'] = datetime.now().isoformat()
    rules.append(rule)
    save_rules(rules)
    return {"message": "Rule created successfully", "rule": rule}

@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: int, rule: dict):
    """Update an existing rule"""
    rules = load_rules()
    for i, r in enumerate(rules):
        if r.get('id') == rule_id:
            rules[i] = {**r, **rule, 'id': rule_id}
            save_rules(rules)
            return {"message": "Rule updated successfully", "rule": rules[i]}
    raise HTTPException(status_code=404, detail="Rule not found")

@app.delete("/api/rules/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete a rule"""
    rules = load_rules()
    rules = [r for r in rules if r.get('id') != rule_id]
    save_rules(rules)
    return {"message": "Rule deleted successfully"}

@app.get("/api/cache-info")
async def get_cache_info():
    """Get cache statistics (for debugging)"""
    return {
        "cache_size": len(cache),
        "max_size": cache.maxsize,
        "ttl_seconds": cache.ttl,
        "cached_items": list(cache.keys())
    }

# Mount static files
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

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

# Run server
if __name__ == "__main__":
    print("🚀 Starting Apertura Finance API Server...")
    print("📊 Dashboard: http://localhost:8080/dashboard.html")
    print("📰 News: http://localhost:8080/news.html")
    print("💰 Pricing: http://localhost:8080/pricing.html")
    print("🔔 Rules: http://localhost:8080/rules.html")
    uvicorn.run(app, host="0.0.0.0", port=8080)
