import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai
import streamlit.components.v1 as components

# 1. PAGE SETUP
st.set_page_config(layout="wide", page_title="AI Trading Agent")

# 3. RATING LOGIC
def get_detailed_rating(val, metric_type):
    if val == 0 or val is None: return "⚪ N/A", 0
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value: Stock is 'on sale' vs earnings.", 33
        if val < 40: return "⚖️ Average: Priced where it should be.", 15
        return "⚠️ Pricey: Stock might be too expensive.", 0
        
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power: Company is efficient.", 34
        if val > 8: return "⚖️ Average: Standard performance.", 15
        return "🐌 Slow: Company is getting 'lazy' with money.", 0

    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Safe: Low debt risk.", 33
        if val < 1.6: return "⚖️ Average: Manageable debt.", 15
        return "🚩 Risky Debt: High danger if economy crashes.", 0

# 4. SIDEBAR
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Ticker", "Type the Symbol here").upper()
    run_btn = st.button("🚀 Run Analysis")

if run_btn:
    if not api_key:
        st.error("Missing API Key!")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="2y")

            # A. HEADER & CHART
            st.title(f"📈 {ticker_input} Analysis")
            tradingview_chart(ticker_input)

            # B. CALCULATE SCORES
            f_pe = info.get('forwardPE', 0)
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100
            
            pe_label, pe_score = get_detailed_rating(f_pe, "PE")
            roe_label, roe_score = get_detailed_rating(roe, "ROE")
            debt_label, debt_score = get_detailed_rating(debt, "DEBT")
            
            final_score = pe_score + roe_score + debt_score

            # C. FINAL SCORE DASHBOARD
            st.divider()
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Total Investment Score", f"{final_score}/100")
                if final_score >= 80:
                    st.success("💎 STRONG CALL CANDIDATE")
                elif final_score >= 40:
                    st.warning("⚖️ AVERAGE / HOLD")
                else:
                    st.error("🚩 AVOID / HIGH RISK")
            
            with col2:
                st.info("**💡 Pro Tip for the 'Call':** If your goal is to buy a Call option, you want all three metrics to be Green. If any metric is Red, it's safer to wait.")

            # D. RATINGS TABLE
            st.subheader("🚦 Rating Breakdown")
            rating_df = pd.DataFrame({
                "Metric": ["Valuation (P/E)", "Efficiency (ROE)", "Safety (Debt/Eq)"],
                "Status": [pe_label, roe_label, debt_label]
            })
            st.table(rating_df)

            # E. MOMENTUM TABLE
            st.subheader("📊 Price Momentum")
            # Using simple slicing for history
            mom_df = pd.DataFrame({
                "Timeframe": ["1 Week", "1 Month", "1 Year"],
                "Change": [
                    f"{((hist['Close'].iloc[-1]-hist['Close'].iloc[-5])/hist['Close'].iloc[-5])*100:.2f}%",
                    f"{((hist['Close'].iloc[-1]-hist['Close'].iloc[-21])/hist['Close'].iloc[-21])*100:.2f}%",
                    f"{((hist['Close'].iloc[-1]-hist['Close'].iloc[-252])/hist['Close'].iloc[-252])*100:.2f}%"
                ]
            })
            st.table(mom_df)

            # F. AI VERDICT
            with st.spinner("AI Analyst reading the data..."):
                client = genai.Client(api_key=api_key)
                prompt = f"Analyze {ticker_input}. Score: {final_score}/100. PE: {f_pe}, ROE: {roe}%, Debt: {debt}. Verdict: BUY, HOLD, or AVOID?"
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                st.subheader("🤖 AI Executive Summary")
                st.write(response.text)

        except Exception as e:
            st.error(f"Error: {e}")
