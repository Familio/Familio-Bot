import streamlit as st
import yfinance as yf
from google import genai
import pandas as pd

# 1. THE SAFETY LIGHT
st.title("🤖 My Trading Agent")
st.success("The clubhouse is open! Ready for analysis.")

# 2. THE SIDEBAR (Where your inputs are)
with st.sidebar:
    st.header("Settings")
    # You can get your key at aistudio.google.com
    api_key = st.text_input("Paste Gemini API Key", type="password")
    ticker = st.text_input("Stock Ticker", "TSM")
    run_button = st.button("Analyze Stock")

# 3. THE LOGIC
if run_button:
    if not api_key:
        st.error("Please paste your Gemini API Key in the sidebar!")
    else:
        try:
            # Check if Gemini works
            client = genai.Client(api_key=api_key)
            
            # Get Data
            st.write(f"🔍 Fetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Show a simple table first
            st.subheader(f"Data for {ticker}")
            metrics = {
                "P/E Ratio": info.get("trailingPE"),
                "ROE": info.get("returnOnEquity"),
                "Debt/Equity": info.get("debtToEquity"),
                "Margin": info.get("profitMargins")
            }
            st.table(pd.DataFrame([metrics]))
            
            # Ask Gemini
            prompt = f"Analyze {ticker} with these metrics: {metrics}. Tell me: BUY, SELL, or HOLD?"
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            
            st.subheader("Gemini's Verdict")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"Something went wrong: {e}")
