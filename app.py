import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

st.set_page_config(layout="wide") # Makes the table easier to read
st.title("🚀 Professional Stock Scanner")

# SIDEBAR SETTINGS
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Enter Symbol", "TSM").upper()
    run_btn = st.button("Run Full Analysis")

def get_change(history, days):
    """Calculates percentage change based on number of days"""
    try:
        current = history['Close'].iloc[-1]
        past = history['Close'].iloc[-days-1] if len(history) > days else history['Close'].iloc[0]
        return ((current - past) / past) * 100
    except: return 0

if run_btn:
    if not api_key:
        st.error("Please enter your API Key!")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            # Fetch 5 years of history for the long-term changes
            hist = stock.history(period="5y")

            # 1. CALCULATE PRICE CHANGES
            change_24h = get_change(hist, 1)
            change_3d = get_change(hist, 3)
            change_1w = get_change(hist, 5) # 5 trading days in a week
            change_1m = get_change(hist, 21)
            change_3m = get_change(hist, 63)
            change_6m = get_change(hist, 126)
            change_1y = get_change(hist, 252)
            change_5y = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100

            # 2. ORGANIZE DATA INTO A TABLE
            data = {
                "Metric": ["Price", "Volume", "Market Cap", "P/E (TTM)", "Forward P/E", "Debt/Equity", "Profit Margin", "ROE", "ROA"],
                "Value": [
                    f"${info.get('currentPrice', 0):,.2f}",
                    f"{info.get('volume', 0):,}",
                    f"${info.get('marketCap', 0):,}",
                    info.get('trailingPE', 'N/A'),
                    info.get('forwardPE', 'N/A'),
                    info.get('debtToEquity', 'N/A'),
                    f"{info.get('profitMargins', 0)*100:.2f}%",
                    f"{info.get('returnOnEquity', 0)*100:.2f}%",
                    f"{info.get('returnOnAssets', 0)*100:.2f}%"
                ]
            }

            perf = {
                "Timeframe": ["24h", "3 Day", "1 Week", "1 Month", "3 Month", "6 Month", "1 Year", "5 Year"],
                "Change %": [f"{change_24h:.2f}%", f"{change_3d:.2f}%", f"{change_1w:.2f}%", f"{change_1m:.2f}%", 
                             f"{change_3m:.2f}%", f"{change_6m:.2f}%", f"{change_1y:.2f}%", f"{change_5y:.2f}%"]
            }

            # DISPLAY TABLES
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Fundamentals")
                st.table(pd.DataFrame(data))
            with col2:
                st.subheader("Price Performance")
                st.table(pd.DataFrame(perf))

            # 3. AI VERDICT
            client = genai.Client(api_key=api_key)
            prompt = f"Act as a financial analyst. Based on these metrics for {ticker_input}: {data} and {perf}, give me a detailed BUY/SELL/HOLD verdict."
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            
            st.divider()
            st.subheader("🤖 AI Analyst Verdict")
            st.write(response.text)

        except Exception as e:
            st.error(f"Error: {e}")
