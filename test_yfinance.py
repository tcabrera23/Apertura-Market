import yfinance as yf
import pandas as pd
import json
from datetime import datetime

def test_yfinance_analysis(ticker_symbol):
    print(f"--- Testing {ticker_symbol} ---")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Recommendations
    print("\n1. Recommendations:")
    try:
        recs = ticker.recommendations
        if recs is not None and not recs.empty:
            print(recs.tail())
        else:
            print("No recommendations data (empty/None)")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Earnings Estimate
    print("\n2. Earnings Estimate:")
    try:
        # Note: 'earnings_estimate' might not be a direct property on Ticker, usually it's in 'analysis' if using older versions or different structure.
        # But yfinance often exposes it via other ways or it might be broken.
        # Let's check 'earnings_dates' or 'calendar'
        calendar = ticker.calendar
        print("Calendar:", calendar)
        
        # Let's try to find where earnings estimates live. 
        # Often it's `ticker.earnings_estimate` (if it exists) or scraping is needed.
        # Check standard properties
        print("Earnings History:", ticker.earnings_history)
        print("Earnings Dates:", ticker.earnings_dates)
        
    except Exception as e:
        print(f"Error checking earnings: {e}")

    # 3. Revenue vs Earnings (Financials)
    print("\n3. Financials (Revenue/Earnings):")
    try:
        fin = ticker.quarterly_financials
        if fin is not None and not fin.empty:
            print(fin.loc[['Total Revenue', 'Net Income']])
        else:
            print("No quarterly financials")
    except Exception as e:
        print(f"Error: {e}")
        
    # 4. Info (for general sentiment/recommendation key)
    print("\n4. Info:")
    try:
        info = ticker.info
        print("Recommendation Key:", info.get('recommendationKey'))
        print("Target Mean Price:", info.get('targetMeanPrice'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_yfinance_analysis("NVDA")

