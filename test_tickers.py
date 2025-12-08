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
    "GGAL": "Grupo Financiero Galicia",
    "PAM": "Pampa Energia",
    "MELI": "MercadoLibre",
    "BMA": "Banco Macro",
    "SUPV": "Supervielle",
    "TEO": "Telecom Argentina",
    "LOMA": "Loma Negra",
    "CRESY": "Cresud",
    "BBAR": "BBVA Argentina"
}

for ticker, name in argentina_tickers.items():
    result = test_ticker(ticker)
    print(f"{ticker:8} | {name:35} | {result}")

# Tickers de Portfolio (solo los problemáticos)
print("\n" + "=" * 60)
print("PORTFOLIO ASSETS (Verificando problemáticos)")
print("=" * 60)
portfolio_problematic = {
    "VISTA": "Vista Energy",
    "VIST": "Vista&Gas (antiguo)",
    "DESP": "Despegar.com",
    "BAYRY": "Bayer"
}

for ticker, name in portfolio_problematic.items():
    result = test_ticker(ticker)
    print(f"{ticker:8} | {name:35} | {result}")

print("\n" + "=" * 60)
print("PRUEBAS COMPLETAS")
print("=" * 60)

