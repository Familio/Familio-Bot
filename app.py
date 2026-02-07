import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="AI Stock Terminal")

# --- 2. TRADINGVIEW CHART FUNCTION ---
def tradingview_chart(symbol):
    """Creates a large, interactive TradingView chart"""
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:800px;width:100%;">
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
    components.html(tv_html, height=800)

# --- 3. HELPER FUNCTIONS ---
def get_pct(hist, days):
    """Calculates price change percentage"""
    try:
        start = hist['Close'].iloc[-days-1]
        end = hist['Close'].iloc[-1]
        return ((end - start) / start) * 100
    except: return 0

# --- 4. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Paste Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Ticker", "TSM").upper()
    run_btn = st.button("🚀 Run Full Analysis")

# --- 5. MAIN APP LOGIC ---
if run_btn:
    if not api_key:
        st.error("Missing API Key! Please paste it in the sidebar.")
    else:
        try:
            # Fetch Data
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="5y") # 5 years for full history

            # A. HEADER & CHART
            st.title(f"📈 {ticker_input} - {info.get('longName', 'Stock Analysis')}")
            tradingview_chart(ticker_input)

            # B. MARKET MOMENTUM TABLE
            st.divider()
            st.subheader("📊 Market Cap & Price Momentum")
            
            mkt_data = {
                "Metric": ["Market Cap", "Trading Volume", "24h Change", "1 Week Change", "1 Month Change", "6 Month Change", "1 Year Change", "5 Year Change"],
                "Value": [
                    f"${info.get('marketCap', 0):,}",
                    f"{info.get('volume', 0):,}",
                    f"{get_pct(hist, 1):.2f}%",
                    f"{get_pct(hist, 5):.2f}%",
                    f"{get_pct(hist, 21):.2f}%",
                    f"{get_pct(hist, 126):.2f}%",
                    f"{get_pct(hist, 252):.2f}%",
                    f"{((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100:.2f}%"
                ]
            }
            st.table(pd.DataFrame(mkt_data))

            # C. FUNDAMENTALS & RATINGS TABLE
            st.subheader("🏛️ Financial Health & Ratings")
            
            # Math for ratios
            pe_ttm = info.get('trailingPE', 0)
            f_pe = info.get('forwardPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            roa = info.get('returnOnAssets', 0) * 100
            debt_eq = info.get('debtToEquity', 0) / 100
            margin = info.get('profitMargins', 0) * 100

            # Condition Logic
            pe_cond = "✅ Good" if f_pe < 20 else "⚖️ Average" if f_pe < 35 else "❌ High"
            roe_cond = "✅ Strong" if roe > 20 else "⚖️ Average" if roe > 10 else "❌ Weak"
            debt_cond = "✅ Safe" if debt_eq < 0.8 else "⚖️ Average" if debt_eq < 1.5 else "❌ Risky"

            fun_data = {
                "Financial Metric": ["P/E Ratio (TTM)", "Forward P/E", "ROE", "ROA", "Debt/Equity", "Net Profit Margin"],
                "Current Value": [f"{pe_ttm:.2f}", f"{f_pe:.2f}", f"{roe:.2f}%", f"{roa:.2f}%", f"{debt_eq:.2f}", f"{margin:.2f}%"],
                "Condition": [pe_cond, pe_cond, roe_cond, "N/A", debt_cond, "N/A"]
            }
            st.table(pd.DataFrame(fun_data))

            # D. FINAL AI SUMMARY VERDICT
            st.divider()
            st.subheader(f"🏁 Final AI Investment Verdict: {ticker_input}")
            
            with st.spinner("AI Analyst is thinking..."):
                client = genai.Client(api_key=api_key)
                
                # Build the Mega-Prompt
                analysis_prompt = f"""
                Act as a professional Stock Analyst. Analyze {ticker_input} based on:
                - Forward P/E: {f_pe} ({pe_cond})
                - ROE: {roe:.2f}% ({roe_cond})
                - Debt/Equity: {debt_eq:.2f} ({debt_cond})
                - 1-Month Momentum: {get_pct(hist, 21):.2f}%
                - 1-Year Momentum: {get_pct(hist, 252):.2f}%
                
                Tell the user if they should BUY, HOLD, or IGNORE FOR NOW. 
                Explain why in a short paragraph and list the biggest risk.
                """
                
                response = client.models.generate_content(model="gemini-1.5-flash", contents=analysis_prompt)
                verdict_text = response.text
                
                # Visual Alert Boxes
                if "BUY" in verdict_text.upper():
                    st.success("🟢 AI SUGGESTION: BUY / FAVORABLE")
                elif "HOLD" in verdict_text.upper():
                    st.warning("🟡 AI SUGGESTION: HOLD / NEUTRAL")
                else:
                    st.error("🔴 AI SUGGESTION: IGNORE / AVOID")
                
                st.write(verdict_text)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
