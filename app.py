import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

st.set_page_config(layout="wide")
st.title("🤖 AI Stock Agent with Ratings")

# SIDEBAR
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("Analyze Now")

def get_rating(val, metric_type):
    """Returns a rating and color based on industry benchmarks"""
    if val == "N/A" or val is None: return "⚪ Neutral", "gray"
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", "green"
        if val < 35: return "⚖️ Average", "orange"
        return "⚠️ Pricey", "red"
        
    if metric_type == "ROE":
        if val > 20: return "🔥 High Power", "green"
        if val > 10: return "⚖️ Average", "orange"
        return "🐌 Slow", "red"

    if metric_type == "DEBT":
        if val < 0.5: return "🛡️ Very Safe", "green"
        if val < 1.5: return "⚖️ Average", "orange"
        return "🚩 Risky Debt", "red"

if run_btn:
    if not api_key:
        st.error("Please enter your API Key!")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            # --- CALCULATE RATINGS ---
            pe = info.get('forwardPE')
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100 # yfinance debt is often shown as 100-base
            
            pe_label, pe_col = get_rating(pe, "PE")
            roe_label, roe_col = get_rating(roe, "ROE")
            debt_label, debt_col = get_rating(debt, "DEBT")

            # --- DISPLAY DASHBOARD ---
            st.subheader(f"Summary for {ticker_input}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Valuation (P/E)", f"{pe:.2f}" if pe else "N/A", pe_label)
            c2.metric("Efficiency (ROE)", f"{roe:.2f}%", roe_label)
            c3.metric("Safety (Debt/Eq)", f"{debt:.2f}", debt_label)

            # --- DETAILED TABLE ---
            st.divider()
            full_data = {
                "Metric": ["Price", "Forward P/E", "ROE", "Debt/Equity", "Profit Margin", "Net Assets"],
                "Value": [info.get('currentPrice'), pe, f"{roe:.2f}%", debt, f"{info.get('profitMargins',0)*100:.2f}%", info.get('totalAssets')],
                "Status": [ "Current", pe_label, roe_label, debt_label, "N/A", "N/A"]
            }
            st.table(pd.DataFrame(full_data))

            # --- UPDATED AI VERDICT SECTION ---
            client = genai.Client(api_key=api_key)
            
            # We build a super-prompt that includes EVERYTHING from your tables
            analysis_prompt = f"""
            Act as a professional Stock Analyst. Analyze {ticker_input} based on these specific data points:
            
            1. FUNDAMENTALS:
               - Forward P/E: {pe} ({pe_r})
               - ROE: {roe:.2f}% ({roe_r})
               - Debt/Equity: {debt:.2f} ({debt_r})
               - Net Profit Margin: {info.get('profitMargins', 0)*100:.2f}%
            
            2. MOMENTUM & MARKET:
               - Market Cap: ${info.get('marketCap', 0):,}
               - 1-Month Change: {get_pct(hist, 21):.2f}%
               - 1-Year Change: {get_pct(hist, 252):.2f}%
            
            Based on this data, provide:
            - A 'FINAL RATING' (BUY, HOLD, or IGNORE FOR NOW).
            - A 'SUMMARY' explaining why (mentioning if it's too expensive or if the momentum is too fast).
            - A 'RISK LEVEL' (Low, Medium, or High).
            """
            
            response = client.models.generate_content(model="gemini-1.5-flash", contents=analysis_prompt)
            
            # Displaying the summary in a nice box
            st.divider()
            st.subheader(f"🏁 Final AI Investment Summary: {ticker_input}")
            
            # Using st.info or st.success based on the rating to make it look pro
            verdict_text = response.text
            if "BUY" in verdict_text.upper():
                st.success("🟢 AI SUGGESTION: BUY")
            elif "HOLD" in verdict_text.upper():
                st.warning("🟡 AI SUGGESTION: HOLD / AVERAGE")
            else:
                st.error("🔴 AI SUGGESTION: IGNORE / AVOID")
                
            st.write(verdict_text)
