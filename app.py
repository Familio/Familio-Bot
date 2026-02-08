import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

# --- 2. UPDATED RATING LOGIC (Now 25 pts each) ---
def get_rating(val, metric_type):
    """Calculates status and points for a 4-indicator model (25 pts each)"""
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0
    
    # Each category now scales to 25 points to maintain a 100-point total
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 25
        if val < 40: return "⚖️ Average", 12
        return "⚠️ Pricey", 0
        
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 25
        if val > 8: return "⚖️ Average", 12
        return "🐌 Slow", 0

    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 25
        if val < 1.6: return "⚖️ Average", 12
        return "🚩 Risky Debt", 0

    if metric_type == "PS":
        if val < 2.0: return "✅ Fair Sales", 25
        if val < 5.0: return "⚖️ Moderate", 12
        return "⚠️ High Premium", 0

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
            # 4a. Extract Data
            trailing_pe = info.get('trailingPE')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            ps_ratio = info.get('priceToSalesTrailing12Months')
            pb_ratio = info.get('priceToBook') # Still fetched for display, but not scored

            # 4b. Calculate Recalibrated Scores (4 metrics x 25 pts = 100 pts)
            pe_label, pe_score = get_rating(trailing_pe, "PE")
            roe_label, roe_score = get_rating(roe, "ROE")
            debt_label, debt_score = get_rating(debt, "DEBT")
            ps_label, ps_score = get_rating(ps_ratio, "PS")
            
            total_score = pe_score + roe_score + debt_score + ps_score
            
            if total_score >= 75: total_status = "💎 Strong Buy Candidate"
            elif total_score >= 45: total_status = "⚖️ Average / Hold"
            else: total_status = "🚩 High Risk / Avoid"

            # --- 5. VISUALS (Candlestick) ---
            st.subheader(f"Price Action: {ticker_input}")
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index, open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close']
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # --- 6. DATA TABLE ---
            st.divider()
            st.subheader("Fundamental Scorecard (P/B Excluded from Score)")
            
            full_data = {
                "Metric": ["P/E (TTM)", "P/S Ratio", "ROE %", "Debt/Equity", "P/B Ratio (Info Only)", "OVERALL SCORE"],
                "Value": [
                    f"{trailing_pe:.2f}" if trailing_pe else "N/A",
                    f"{ps_ratio:.2f}" if ps_ratio else "N/A",
                    f"{roe:.2f}%", 
                    f"{debt:.2f}",
                    f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                    f"{total_score}/100"
                ],
                "Status": [pe_label, ps_label, roe_label, debt_label, "Not Scored", total_status]
            }
            st.table(pd.DataFrame(full_data))

            # --- 7. REVISED METHODOLOGY ---
            with st.expander("🚦 Deep Dive: Recalibrated Scoring (No P/B)"):
                st.markdown(f"""
                ### Why exclude P/B?
                For tech and service-heavy stocks, **Price-to-Book** is often irrelevant because their value is in "intangibles" (IP, Brand, Code) rather than physical assets.
                
                **New Calculation Formula (25% Weight per Indicator):**
                $Total Score = S_{{PE}} + S_{{PS}} + S_{{ROE}} + S_{{DEBT}}$
                
                | Indicator | ✅ 25 Points | ⚖️ 12 Points | ⚠️ 0 Points |
                | :--- | :--- | :--- | :--- |
                | **P/E Ratio** | < 20 | 20 - 40 | > 40 |
                | **P/S Ratio** | < 2.0 | 2.0 - 5.0 | > 5.0 |
                | **ROE %** | > 18% | 8% - 18% | < 8% |
                | **Debt/Equity**| < 0.8 | 0.8 - 1.6 | > 1.6 |
                """)
    except Exception as e:
        st.error(f"Error: {e}")
