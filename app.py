import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Advanced Stock Analysis")

# --- 3. RATING LOGIC ---
def get_rating(val, metric_type):
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 33
        if val < 40: return "⚖️ Average", 15
        return "⚠️ Pricey", 0
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 34
        if val > 8: return "⚖️ Average", 15
        return "🐌 Slow", 0
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 33
        if val < 1.6: return "⚖️ Average", 15
        return "🚩 Risky Debt", 0

# --- 4. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Analyze Now")

# --- 5. MAIN APP LOGIC ---
if run_btn:
    if not api_key:
        st.error("Please enter your API Key in the sidebar!")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            # Data Extraction
            mkt_cap = info.get('marketCap', 0)
            trailing_pe = info.get('trailingPE')
            f_pe = info.get('forwardPE')
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100
            cap_str = f"${mkt_cap/1e12:.2f}T" if mkt_cap >= 1e12 else f"${mkt_cap/1e9:.2f}B"

            # --- 1. CALCULATE INDIVIDUAL SCORES ---
            pe_label, pe_score = get_rating(f_pe, "PE")
            roe_label, roe_score = get_rating(roe, "ROE")
            debt_label, debt_score = get_rating(debt, "DEBT")
            
            # --- 2. CALCULATE OVERALL SCORE ---
            total_score = pe_score + roe_score + debt_score
            
            if total_score >= 80:
                total_status = "💎 Strong Buy Candidate"
            elif total_score >= 40:
                total_status = "⚖️ Average / Hold"
            else:
                total_status = "🚩 High Risk / Avoid"

            # Display Visuals
            st.subheader(f"Analysis for {ticker_input}")
            tradingview_chart(ticker_input)

            # --- 3. ADD TO THE TABLE ---
            st.divider()
            full_data = {
                "Metric": [
                    "Current Price", 
                    "Market Cap",
                    "Price/Earning (TTM)"
                    "Forward P/E", 
                    "Return on Equity (ROE)", 
                    "Debt/Equity", 
                    "OVERALL SCORE"
                ],
                "Value": [
                    f"${info.get('currentPrice')}", 
                    cap_str,
                    f"{f_pe:.2f}" if f_pe else "N/A", 
                    f"{roe:.2f}%", 
                    f"{debt:.2f}", 
                    f"{total_score}/100"
                ],
                "Status": [
                    "Current", 
                    "Size", 
                    pe_label, 
                    roe_label, 
                    debt_label, 
                    total_status
                ]
            }
            st.table(pd.DataFrame(full_data))

            # --- EDUCATIONAL FOOTER ---
            st.divider()
            with st.expander("🚦 Methodology & Evaluation Breakdown"):
                st.markdown(f"""
                **How your {total_score}/100 score is calculated:**
                1. **Valuation (33 pts):** Points awarded if Forward P/E is under 20.
                2. **Efficiency (34 pts):** Points awarded if ROE is above 18%.
                3. **Safety (33 pts):** Points awarded if Debt/Equity is below 0.8.
                """)
                    # --- 6. EDUCATIONAL FOOTER ---
            st.divider()
            with st.expander("🚦 How to Read the Ratings & Methodology"):
                st.markdown("""
                ### 📊 Understanding the Metrics
                * **Valuation (P/E):** Compares share price to earnings. 
                    * *✅ Good Value (<20):* The stock is "on sale" compared to its profits.
                    * *⚠️ Pricey (>35):* You are paying a high premium for every $1 of profit.
                * **Efficiency (ROE):** Shows how well the company uses your money to make profit.
                    * *🔥 High Power (>20%):* Exceptional management and high profitability.
                    * *🐌 Slow (<10%):* The company is struggling to generate returns on shareholder capital.
                * **Safety (Debt/Equity):** Measures financial risk.
                    * *🛡️ Very Safe (<0.5):* The company has very little debt compared to its assets.
                    * *🚩 Risky Debt (>1.5):* The company is heavily leveraged; risky if interest rates rise.
         """)
        except Exception as e:
            st.error(f"Error: {e}")
