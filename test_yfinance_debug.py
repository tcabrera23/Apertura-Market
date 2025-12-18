import yfinance as yf
import json

def test_yfinance(ticker):
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    
    data = {}
    
    # 1. Analysis / Recommendations
    try:
        print("Fetching recommendations...")
        recs = stock.recommendations
        if recs is not None and not recs.empty:
            print("Recommendations found (head):")
            print(recs.head())
            # Latest recommendations
            latest = recs.iloc[-1]
            data['recommendations'] = latest.to_dict()
        else:
            print("No recommendations found.")
    except Exception as e:
        print(f"Error fetching recommendations: {e}")

    # 2. Earnings History (EPS Trend)
    try:
        print("Fetching earnings_history...")
        eh = stock.earnings_history
        if eh is not None and not eh.empty:
            print("Earnings History found:")
            print(eh)
            data['earnings_history'] = eh.to_dict(orient='records')
        else:
            print("No earnings history found.")
    except Exception as e:
        print(f"Error fetching earnings_history: {e}")
        
    # 3. Calendar (Revenue vs Earnings Estimates sometimes here)
    try:
        print("Fetching calendar...")
        cal = stock.calendar
        if cal is not None:
             print("Calendar found:")
             print(cal)
             data['calendar'] = cal
        else:
            print("No calendar found.")
    except Exception as e:
        print(f"Error fetching calendar: {e}")

    # 4. Income Statement (Revenue vs Earnings - Actuals)
    try:
        print("Fetching financials...")
        fin = stock.quarterly_financials
        if fin is not None and not fin.empty:
            print("Financials found:")
            print(fin.iloc[:, :2]) # First two columns
            data['financials'] = fin.to_dict()
        else:
            print("No financials found.")
    except Exception as e:
         print(f"Error fetching financials: {e}")

    return data

if __name__ == "__main__":
    test_yfinance("NVDA")

