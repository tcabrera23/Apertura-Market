#!/usr/bin/env python3
"""
Script rápido para verificar que los tickers son válidos en Yahoo Finance
"""
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

def test_ticker(ticker, timeout=10):
    """Prueba un ticker con timeout"""
    def fetch():
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1d")
        return len(info) > 0 and not hist.empty
    
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(fetch)
        result = future.result(timeout=timeout)
        return "✅ OK" if result else "❌ Sin datos"
    except FuturesTimeoutError:
        return "⏱️ Timeout"
    except Exception as e:
        return f"❌ Error: {str(e)[:50]}"
    finally:
        executor.shutdown(wait=False)

# Tickers de Argentina
print("=" * 60)
print("ARGENTINA ASSETS")
print("=" * 60)
argentina_tickers = {
    "YPF": "YPF",
    "GGAL": "Grupo Financiero Galicia"
}

for ticker, name in argentina_tickers.items():
    result = test_ticker(ticker)
    print(f"{ticker:8} | {name:35} | {result}")

# Tickers de Portfolio (solo los problemáticos)
print("\n" + "=" * 60)
print("PORTFOLIO ASSETS (Verificando problemáticos)")
print("=" * 60)
portfolio_problematic = {
    "PFE": "Pfizer",
    "AMD": "AMD",
    "BABA": "Alibaba",
    "SPY": "SPDR S&P 500 ETF",
    "QQQ": "Invesco QQQ Trust",
    "GLD": "SPDR Gold Trust",
    "DIA": "SPDR Dow Jones Industrial Average ETF",
    "FXI": "iShares China Large-Cap ETF",
    "MCD": "McDonald's",
    "NFLX": "Netflix",
    "V": "Visa",
    "UBER": "Uber Technologies",
    "DIS": "Walt Disney",
    "SPOT": "Spotify Technology",
    "BAC": "Bank of America",
    "ABNB": "Airbnb",
    "KO": "Coca-Cola",
    "PLTR": "Palantir Technologies",
    "INTC": "Intel",
    "AVGO": "Broadcom",
    "WMT": "Walmart",
    "UNH": "UnitedHealth Group",
    "JPM": "JPMorgan Chase",
    "BAYRY": "Bayer",
    "F": "Ford Motor"
}
for ticker, name in portfolio_problematic.items():
    result = test_ticker(ticker)
    print(f"{ticker:8} | {name:35} | {result}")

print("\n" + "=" * 60)
print("PRUEBAS COMPLETAS")
print("=" * 60)

