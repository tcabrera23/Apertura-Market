from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
from cachetools import TTLCache
import uvicorn
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json
import os
import re
from groq import Groq

# Initialize FastAPI app
app = FastAPI(
    title="BullAnalytics API",
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
    # Technical analysis metrics
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    cash_flow: Optional[float] = None
    dividend_yield: Optional[float] = None
    year_low: Optional[float] = None
    year_high: Optional[float] = None
    avg_volume: Optional[float] = None
    # Technical indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    # Fundamental metrics - Revenue & Growth
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    revenue_quarterly_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None
    # Fundamental metrics - Profitability
    profit_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    # Fundamental metrics - Returns
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    # Fundamental metrics - Valuation
    price_to_book: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    enterprise_value: Optional[float] = None
    enterprise_to_revenue: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None
    # Fundamental metrics - Financial Health
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    total_assets: Optional[float] = None
    book_value: Optional[float] = None
    # Risk metrics
    beta: Optional[float] = None
    # Logo URL
    logo_url: Optional[str] = None

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
        
        # Get logo URL if available
        logo_url = info.get('logo_url') or info.get('website')
        
        if hist.empty:
            return None
        
        all_time_high = hist['High'].max()
        all_time_low = hist['Low'].min()
        current_price = hist['Close'].iloc[-1]
        diff_from_max = (current_price - all_time_high) / all_time_high
        pe_ratio = info.get('trailingPE')
        
        # Get 1 year data for year high/low
        hist_1y = stock.history(period="1y")
        year_high = float(hist_1y['High'].max()) if not hist_1y.empty else None
        year_low = float(hist_1y['Low'].min()) if not hist_1y.empty else None
        
        # Technical metrics
        volume = float(hist['Volume'].iloc[-1]) if not hist.empty else None
        market_cap = info.get('marketCap')
        cash_flow = info.get('operatingCashflow') or info.get('freeCashflow')
        dividend_yield = info.get('dividendYield')
        avg_volume = info.get('averageVolume')
        
        # Fundamental metrics - Revenue & Growth
        revenue = info.get('totalRevenue')
        revenue_growth = info.get('revenueGrowth')
        revenue_quarterly_growth = info.get('revenueQuarterlyGrowth')
        earnings_growth = info.get('earningsGrowth')
        earnings_quarterly_growth = info.get('earningsQuarterlyGrowth')
        
        # Fundamental metrics - Profitability
        profit_margin = info.get('profitMargins')
        gross_margin = info.get('grossMargins')
        operating_margin = info.get('operatingMargins')
        ebitda = info.get('ebitda')
        net_income = info.get('netIncomeToCommon')
        
        # Fundamental metrics - Returns
        return_on_assets = info.get('returnOnAssets')
        return_on_equity = info.get('returnOnEquity')
        
        # Fundamental metrics - Valuation
        price_to_book = info.get('priceToBook')
        forward_pe = info.get('forwardPE')
        peg_ratio = info.get('pegRatio')
        enterprise_value = info.get('enterpriseValue')
        enterprise_to_revenue = info.get('enterpriseToRevenue')
        enterprise_to_ebitda = info.get('enterpriseToEbitda')
        
        # Fundamental metrics - Financial Health
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        total_debt = info.get('totalDebt')
        total_cash = info.get('totalCash')
        total_assets = info.get('totalAssets')
        book_value = info.get('bookValue')
        
        # Risk metrics
        beta = info.get('beta')
        
        # Try to get additional data from financial statements if not in info
        try:
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            if financials is not None and not financials.empty:
                # Get most recent year's data
                if revenue is None and 'Total Revenue' in financials.index:
                    revenue = float(financials.loc['Total Revenue'].iloc[0]) if not financials.loc['Total Revenue'].empty else None
                if net_income is None and 'Net Income' in financials.index:
                    net_income = float(financials.loc['Net Income'].iloc[0]) if not financials.loc['Net Income'].empty else None
            
            if balance_sheet is not None and not balance_sheet.empty:
                if total_debt is None and 'Total Debt' in balance_sheet.index:
                    total_debt = float(balance_sheet.loc['Total Debt'].iloc[0]) if not balance_sheet.loc['Total Debt'].empty else None
                if total_cash is None and 'Cash And Cash Equivalents' in balance_sheet.index:
                    total_cash = float(balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]) if not balance_sheet.loc['Cash And Cash Equivalents'].empty else None
                if total_assets is None and 'Total Assets' in balance_sheet.index:
                    total_assets = float(balance_sheet.loc['Total Assets'].iloc[0]) if not balance_sheet.loc['Total Assets'].empty else None
                if book_value is None and 'Stockholders Equity' in balance_sheet.index:
                    book_value = float(balance_sheet.loc['Stockholders Equity'].iloc[0]) if not balance_sheet.loc['Stockholders Equity'].empty else None
            
            if cashflow is not None and not cashflow.empty:
                if cash_flow is None and 'Operating Cash Flow' in cashflow.index:
                    cash_flow = float(cashflow.loc['Operating Cash Flow'].iloc[0]) if not cashflow.loc['Operating Cash Flow'].empty else None
        except Exception as e:
            print(f"Error fetching financial statements for {ticker}: {e}")
        
        # Calculate technical indicators (simplified)
        # RSI calculation (14 period)
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
        
        # MACD (simplified: 12-26 EMA difference)
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
            # Fundamental metrics
            revenue=float(revenue) if revenue else None,
            revenue_growth=float(revenue_growth) if revenue_growth else None,
            revenue_quarterly_growth=float(revenue_quarterly_growth) if revenue_quarterly_growth else None,
            earnings_growth=float(earnings_growth) if earnings_growth else None,
            earnings_quarterly_growth=float(earnings_quarterly_growth) if earnings_quarterly_growth else None,
            profit_margin=float(profit_margin) if profit_margin else None,
            gross_margin=float(gross_margin) if gross_margin else None,
            operating_margin=float(operating_margin) if operating_margin else None,
            ebitda=float(ebitda) if ebitda else None,
            net_income=float(net_income) if net_income else None,
            return_on_assets=float(return_on_assets) if return_on_assets else None,
            return_on_equity=float(return_on_equity) if return_on_equity else None,
            price_to_book=float(price_to_book) if price_to_book else None,
            forward_pe=float(forward_pe) if forward_pe else None,
            peg_ratio=float(peg_ratio) if peg_ratio else None,
            enterprise_value=float(enterprise_value) if enterprise_value else None,
            enterprise_to_revenue=float(enterprise_to_revenue) if enterprise_to_revenue else None,
            enterprise_to_ebitda=float(enterprise_to_ebitda) if enterprise_to_ebitda else None,
            debt_to_equity=float(debt_to_equity) if debt_to_equity else None,
            current_ratio=float(current_ratio) if current_ratio else None,
            total_debt=float(total_debt) if total_debt else None,
            total_cash=float(total_cash) if total_cash else None,
            total_assets=float(total_assets) if total_assets else None,
            book_value=float(book_value) if book_value else None,
            beta=float(beta) if beta else None,
            logo_url=logo_url
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

class WatchlistCreate(BaseModel):
    name: str
    assets: Dict[str, str]

@app.post("/api/watchlist")
async def create_watchlist(watchlist: WatchlistCreate):
    """Create or update a custom watchlist"""
    watchlists = load_watchlists()
    watchlists[watchlist.name] = watchlist.assets
    save_watchlists(watchlists)
    return {"message": f"Watchlist '{watchlist.name}' created successfully", "name": watchlist.name}

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
        print(f"Error fetching history for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching history for {ticker}")

@app.get("/api/chart/treemap")
async def get_treemap_chart(category: str = "tracking", metric: str = "market_cap"):
    """Generate treemap chart as image"""
    try:
        # Get data based on category
        data = []
        if category == "tracking":
            for ticker, name in TRACKING_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "portfolio":
            for ticker, name in PORTFOLIO_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "crypto":
            for ticker, name in CRYPTO_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "argentina":
            for ticker, name in ARGENTINA_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        else:
            # Try custom watchlist
            watchlists = load_watchlists()
            if category in watchlists:
                for ticker, name in watchlists[category].items():
                    asset_data = get_asset_data(ticker, name)
                    if asset_data:
                        data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        
        if not data:
            raise HTTPException(status_code=404, detail="Category not found or no data")
        
        # Filter crypto if needed
        is_crypto = category == "crypto"
        if not is_crypto:
            data = [a for a in data if not a.get('ticker', '').endswith('-USD')]
        
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Prepare chart data
        labels = []
        values = []
        for asset in data:
            labels.append(asset.get('ticker', ''))
            if metric == "market_cap":
                values.append(asset.get('market_cap', 0) or 0)
            elif metric == "cash_flow":
                if is_crypto:
                    values.append(asset.get('volume', 0) or 0)
                else:
                    values.append(abs(asset.get('cash_flow', 0) or 0))
            else:
                values.append(0)
        
        # Filter out zero values
        filtered_data = [(l, v) for l, v in zip(labels, values) if v > 0]
        if not filtered_data:
            raise HTTPException(status_code=404, detail="No valid data for chart")
        
        labels, values = zip(*sorted(filtered_data, key=lambda x: x[1], reverse=True))
        
        # Create chart
        plt.style.use('dark_background' if False else 'default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create horizontal bar chart (treemap-like)
        colors = sns.color_palette("Greens", len(labels))
        bars = ax.barh(range(len(labels)), values, color=colors)
        
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel('Value' if metric == "market_cap" else ("Volume" if is_crypto else "Cash Flow"))
        ax.set_title(f"{'Market Cap' if metric == 'market_cap' else ('Volume' if is_crypto else 'Cash Flow')} by Asset")
        ax.grid(axis='x', alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e9:.2f}B' if x >= 1e9 else f'${x/1e6:.2f}M' if x >= 1e6 else f'${x/1e3:.2f}K'))
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return Response(content=img_buffer.getvalue(), media_type="image/png")
        
    except Exception as e:
        print(f"Error generating treemap chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.get("/api/chart/bar")
async def get_bar_chart(category: str = "tracking", metric: str = "revenue_growth"):
    """Generate bar chart as image"""
    try:
        # Get data based on category
        data = []
        if category == "tracking":
            for ticker, name in TRACKING_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "portfolio":
            for ticker, name in PORTFOLIO_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "crypto":
            for ticker, name in CRYPTO_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        elif category == "argentina":
            for ticker, name in ARGENTINA_ASSETS.items():
                asset_data = get_asset_data(ticker, name)
                if asset_data:
                    data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        else:
            # Try custom watchlist
            watchlists = load_watchlists()
            if category in watchlists:
                for ticker, name in watchlists[category].items():
                    asset_data = get_asset_data(ticker, name)
                    if asset_data:
                        data.append(asset_data.model_dump() if hasattr(asset_data, 'model_dump') else asset_data.dict())
        
        if not data:
            raise HTTPException(status_code=404, detail="Category not found or no data")
        
        is_crypto = category == "crypto"
        if not is_crypto:
            data = [a for a in data if not a.get('ticker', '').endswith('-USD')]
        
        if not data:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Prepare data
        labels = []
        values = []
        colors_list = []
        
        for asset in data:
            labels.append(asset.get('ticker', ''))
            value = 0
            if metric == "revenue_growth":
                value = (asset.get('revenue_growth', 0) or 0) * 100
            elif metric == "profit_margin":
                value = (asset.get('profit_margin', 0) or 0) * 100
            elif metric == "roe":
                value = (asset.get('return_on_equity', 0) or 0) * 100
            elif metric == "pe":
                value = asset.get('pe_ratio', 0) or 0
            elif metric == "diff_max":
                value = (asset.get('diff_from_max', 0) or 0) * 100
            
            values.append(value)
            colors_list.append('#22c55e' if value >= 0 else '#ef4444')
        
        # Sort by value
        sorted_data = sorted(zip(labels, values, colors_list), key=lambda x: x[1], reverse=True)
        labels, values, colors_list = zip(*sorted_data)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(labels)), values, color=colors_list)
        
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        metric_titles = {
            "revenue_growth": "Revenue Growth (%)",
            "profit_margin": "Profit Margin (%)",
            "roe": "Return on Equity (ROE) (%)",
            "pe": "P/E Ratio",
            "diff_max": "Difference vs Maximum (%)"
        }
        ax.set_ylabel(metric_titles.get(metric, metric))
        ax.set_title(f"{metric_titles.get(metric, metric)} by Asset")
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return Response(content=img_buffer.getvalue(), media_type="image/png")
        
    except Exception as e:
        print(f"Error generating bar chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@app.get("/api/chart/line")
async def get_line_chart(ticker: str, period: str = "1y"):
    """Generate line chart as image"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval="1d")
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {ticker}")
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(hist.index, hist['Close'], color='#22c55e', linewidth=2, label='Close Price')
        ax.fill_between(hist.index, hist['Close'], alpha=0.3, color='#22c55e')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Price (USD)')
        ax.set_title(f'{ticker} - Historical Price')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis dates
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return Response(content=img_buffer.getvalue(), media_type="image/png")
        
    except Exception as e:
        print(f"Error generating line chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

# News endpoint
@app.get("/api/news")
async def get_news(category: str = "general"):
    """Get financial news from Yahoo Finance RSS with category support"""
    import feedparser
    import re
    
    # Map categories to RSS URLs
    rss_urls = {
        "general": "https://finance.yahoo.com/news/rssindex",
        "crypto": "https://finance.yahoo.com/topic/crypto/rss",
        "tech": "https://finance.yahoo.com/topic/tech/rss",
        "usa": "https://finance.yahoo.com/topic/stock-market-news/rss",
        "china": "https://finance.yahoo.com/topic/china/rss", # Best effort
        "europe": "https://finance.yahoo.com/topic/europe/rss", # Best effort
        "ai": "https://finance.yahoo.com/topic/tech/rss" # Fallback to tech for AI if no specific feed
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

class ChatMessage(BaseModel):
    message: str
    email: Optional[str] = None

@app.post("/api/rules/chat")
async def chat_create_rule(chat_message: ChatMessage):
    """Create a rule from natural language using AI"""
    try:
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
- ticker: El símbolo del activo (ej: NVDA, AAPL, BTC-USD)
- value: El valor numérico de referencia (porcentaje o número según el tipo)
- email: El email del usuario (si se proporciona en el mensaje)

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
            print(f"Groq API error: {e}")
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
            # If JSON parsing fails, try to extract key information manually
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

        # Use provided email or try to extract from rule_data
        email = chat_message.email or rule_data.get("email")
        if not email:
            return {
                "success": False,
                "error": "Se requiere un email para las notificaciones. Por favor, proporciona tu email.",
                "raw_response": response_content
            }

        # Add email to rule
        rule_data["email"] = email

        # Create the rule
        rules = load_rules()
        rule_data["id"] = len(rules) + 1
        rule_data["created_at"] = datetime.now().isoformat()
        rules.append(rule_data)
        save_rules(rules)

        return {
            "success": True,
            "message": "Regla creada exitosamente",
            "rule": rule_data
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Error al parsear la respuesta del AI: {str(e)}",
            "raw_response": response_content if 'response_content' in locals() else None
        }
    except Exception as e:
        print(f"Error in chat_create_rule: {e}")
        return {
            "success": False,
            "error": f"Error al procesar la solicitud: {str(e)}"
        }

@app.get("/api/search-assets")
async def search_assets(query: str):
    """Search for assets using Yahoo Finance autocomplete API"""
    if not query or len(query) < 2:
        return []
    
    try:
        import requests
        import urllib.parse
        
        # Yahoo Finance autocomplete endpoint
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&quotesCount=10&newsCount=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            # Extract quotes from the response
            if 'quotes' in data:
                for quote in data['quotes']:
                    results.append({
                        "symbol": quote.get('symbol', ''),
                        "name": quote.get('longname') or quote.get('shortname', quote.get('symbol', '')),
                        "exchange": quote.get('exchange', ''),
                        "type": quote.get('quoteType', 'EQUITY'),
                        "sector": quote.get('sector', ''),
                        "industry": quote.get('industry', '')
                    })
            
            return results[:10]  # Limit to 10 results
        
        return []
        
    except Exception as e:
        print(f"Error searching assets: {e}")
        return []

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
    print("🚀 Starting BullAnalytics API Server...")
    print("📊 Dashboard: http://localhost:8080/dashboard.html")
    print("📰 News: http://localhost:8080/news.html")
    print("💰 Pricing: http://localhost:8080/pricing.html")
    print("🔔 Rules: http://localhost:8080/rules.html")
    uvicorn.run(app, host="0.0.0.0", port=8080)
