import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

# --- 2. IMPROVED RATING LOGIC ---
def get_rating(val, metric_type, sector="Other"):
    """Calculates status and points with Sector-Awareness"""
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 20
        if val < 40: return "⚖️ Average", 10
        return "⚠️ Pricey", 0
        
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0

    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0

    if metric_type == "PS":
        if val < 2.0: return "✅ Fair Sales", 20
        if val < 5.0: return "⚖️ Moderate", 10
        return "⚠️ High Premium", 0

    if metric_type == "PB":
        # TECH ADJUSTMENT: Tech companies naturally have higher P/B
        if sector in ["Technology", "Communication Services"]:
            if val < 8.0: return "💎 Tech Value", 20
            if val < 15.0: return "⚖️ Tech Fair", 10
            return "⚠️ Asset Heavy", 0
        else:
            # Traditional Value Standards
            if val < 1.5: return "💎 Undervalued", 20
            if val < 4.0: return "⚖️ Fair Assets", 10
            return "⚠️ Asset Heavy", 0

# --- 3. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Control Panel")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="6mo")

        if hist.empty:
            st.error("Could not find data for this symbol.")
        else:
            # 4a. Sector Detection
            stock_sector = info.get('sector', 'Other')
            
            # 4b. Extract Metrics
            trailing_pe = info.get('trailingPE')
            f_pe = info.get('forwardPE')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            ps_ratio = info.get('priceToSalesTrailing12Months')
            pb_ratio = info.get('priceToBook')

            # 4c. Run Scoring with Sector Logic
            pe_label, pe_score = get_rating(trailing_pe, "PE")
            roe_label, roe_score = get_rating(roe, "ROE")
            debt_label, debt_score = get_rating(debt, "DEBT")
            ps_label, ps_score = get_rating(ps_ratio, "PS")
            pb_label, pb_score = get_rating(pb_ratio, "PB", sector=stock_sector)
            
            total_score = pe_score + roe_score + debt_score + ps_score + pb_score
            
            # ... (Visualization and Table code same as before)
            st.subheader(f"Analysis for {info.get('longName')} ({stock_sector})")
            
            # --- 6. DATA TABLE ---
            full_data = {
                "Metric": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity", "TOTAL SCORE"],
                "Value": [f"{trailing_pe:.2f}" if trailing_pe else "N/A", 
                          f"{ps_ratio:.2f}" if ps_ratio else "N/A",
                          f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                          f"{roe:.2f}%", f"{debt:.2f}", f"{total_score}/100"],
                "Status": [pe_label, ps_label, pb_label, roe_label, debt_label, "Rating: " + str(total_score)]
            }
            st.table(pd.DataFrame(full_data))

            # --- 7. METHODOLOGY ---
            with st.expander("🚦 Deep Dive: Scoring Methodology"):
                st.markdown(f"""
                ### Sector-Aware Scoring: {stock_sector}
                Our bot recognizes that **{stock_sector}** companies have different norms.
                * **For Tech:** P/B limits are higher (up to 8.0 for 20 points) because value is in software/patents.
                * **For Others:** Traditional limits apply (P/B < 1.5 for 20 points).
                """)

    except Exception as e:
        st.error(f"Error: {e}")
