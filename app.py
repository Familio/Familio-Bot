import yfinance as yf
import pandas as pd

# 1. Define your watchlist
watchlist = ["TSM", "AAPL", "NVDA", "MSFT", "INTC"]

def analyze_stocks(tickers):
    results = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Pull your specific metrics
        data = {
            "Symbol": ticker,
            "Price": info.get("currentPrice"),
            "Forward P/E": info.get("forwardPE"),
            "ROE (%)": info.get("returnOnEquity", 0) * 100,
            "Margin (%)": info.get("profitMargins", 0) * 100,
            "Debt/Equity": info.get("debtToEquity"),
        }
        
        # 2. THE LOGIC CHECK
        # We define a 'Good Buy' based on your metrics
        is_cheap = data["Forward P/E"] < 25 if data["Forward P/E"] else False
        is_efficient = data["ROE (%)"] > 20
        is_safe = data["Debt/Equity"] < 100 if data["Debt/Equity"] else False
        
        if is_cheap and is_efficient and is_safe:
            data["Verdict"] = "✅ GOOD BUY"
        elif is_efficient:
            data["Verdict"] = "⚖️ HOLD (Pricey)"
        else:
            data["Verdict"] = "❌ AVOID"
            
        results.append(data)
    
    return pd.DataFrame(results)

# Run and show the table
df = analyze_stocks(watchlist)
print(df)
