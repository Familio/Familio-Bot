import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="AI Stock Terminal")

# --- 1. THE TRADINGVIEW CHART FUNCTION ---
def tradingview_chart(symbol):
    # This creates the interactive widget you see on pro sites
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_html, height=500)

# --- 2. THE SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Enter Ticker", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# helper to calculate changes
def get_pct(hist, days):
    try:
        start = hist['Close'].iloc[-days-1]
        end = hist['Close'].iloc[-1]
        return ((end - start) / start) * 100
    except: return 0

# --- 3. MAIN LOGIC ---
if run_btn:
    if not api_key:
        st.warning("Please enter your API Key in the sidebar.")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="2y") # Get enough data for changes

            # A. VISUAL CHART
            st.title(f"📈 {ticker_input} Analysis")
            tradingview_chart(ticker_input)

            # B. MARKET & MOMENTUM TABLE
            st.divider()
            st.subheader("📊 Market & Momentum (History)")
            
            mkt_data = {
                "Timeframe": ["Market Cap", "Daily Volume", "24 Hours", "1 Week", "1 Month", "6 Month", "1 Year"],
                "Value / Change": [
                    f"${info.get('marketCap', 0):,}",
                    f"{info.get('volume', 0):,}",
                    f"{get_pct(hist, 1):.2f}%",
                    f"{get_pct(hist, 5):.2f}%",
                    f"{get_pct(hist, 21):.2f}%",
                    f"{get_pct(hist, 126):.2f}%",
                    f"{get_pct(hist, 252):.2f}%"
                ]
            }
            st.table(pd.DataFrame(mkt_data))

            # C. FUNDAMENTALS TABLE (Good/Average Check)
            st.subheader("🏛️ Fundamentals & Efficiency")
            pe = info.get('forwardPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100
            
            # Simple Logic for the "Rating" column
            pe_r = "✅ Good" if pe < 20 else "⚖️ Average" if pe < 35 else "❌ High"
            roe_r = "✅ Good" if roe > 20 else "⚖️ Average" if roe > 10 else "❌ Weak"
            debt_r = "✅ Safe" if debt < 0.8 else "⚖️ Average" if debt < 1.5 else "❌ Risky"

            fun_data = {
                "Metric": ["Forward P/E", "Return on Equity (ROE)", "Debt to Equity Ratio", "Net Profit Margin"],
                "Current Value": [f"{pe:.2f}", f"{roe:.2f}%", f"{debt:.2f}", f"{info.get('profitMargins', 0)*100:.2f}%"],
                "Condition": [pe_r, roe_r, debt_r, "N/A"]
            }
            st.table(pd.DataFrame(fun_data))

            # D. AI VERDICT
            client = genai.Client(api_key=api_key)
