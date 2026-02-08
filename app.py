import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai

# --- 1. PAGE CONFIGURATION ---
# FIXED: Removed the extra "set" from the function name
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

# ... rest of the code stays the same
# --- 2. RATING LOGIC ---
def get_rating(val, metric_type):
    """Calculates status and points for the overall score (Total 100 pts / 5 metrics = 20 pts each)"""
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
        if val < 1.5: return "💎 Undervalued", 20
        if val < 4.0: return "⚖️ Fair Assets", 10
        return "⚠️ Asset Heavy", 0

# --- 3. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Control Panel")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key!")
    else:
        try:
            # Fetch Data
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="6mo")

            if hist.empty:
                st.error("Could not find data for this symbol. Please check the ticker.")
            else:
                # 4a. Extract Data
                mkt_cap = info.get('marketCap', 0)
                trailing_pe = info.get('trailingPE')
                f_pe = info.get('forwardPE')
                roe = info.get('returnOnEquity', 0) * 100
                debt = info.get('debtToEquity', 0) / 100
                ps_ratio = info.get('priceToSalesTrailing12Months')
                pb_ratio = info.get('priceToBook')
                cap_str = f"${mkt_cap/1e12:.2f}T" if mkt_cap >= 1e12 else f"${mkt_cap/1e9:.2f}B"

                # 4b. Calculate Individual & Total Scores (20 pts each)
                pe_label, pe_score = get_rating(f_pe if f_pe else trailing_pe, "PE")
                roe_label, roe_score = get_rating(roe, "ROE")
                debt_label, debt_score = get_rating(debt, "DEBT")
                ps_label, ps_score = get_rating(ps_ratio, "PS")
                pb_label, pb_score = get_rating(pb_ratio, "PB")
                
                total_score = pe_score + roe_score + debt_score + ps_score + pb_score
                
                # Determine Status
                if total_score >= 80: total_status = "💎 Strong Buy Candidate"
                elif total_score >= 50: total_status = "⚖️ Average / Hold"
                else: total_status = "🚩 High Risk / Avoid"

                # --- 5. VISUALS: CANDLE CHART ---
                st.subheader(f"Price Action: {ticker_input}")
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close']
                )])
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=400)
                st.plotly_chart(fig, use_container_width=True)

                # --- 6. THE DATA TABLE ---
                st.divider()
                st.subheader("Fundamental Scorecard")
                
                full_data = {
                    "Metric": ["P/E (Forward)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity", "OVERALL SCORE"],
                    "Value": [
                        f"{f_pe:.2f}" if f_pe else "N/A", 
                        f"{ps_ratio:.2f}" if ps_ratio else "N/A",
                        f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                        f"{roe:.2f}%", 
                        f"{debt:.2f}", 
                        f"{total_score}/100"
                    ],
                    "Status": [pe_label, ps_label, pb_label, roe_label, debt_label, total_status]
                }
                
                df_display = pd.DataFrame(full_data).astype(str)
                st.table(df_display)

               # --- 8. METHODOLOGY ---
with st.expander("🚦 How to Read the Ratings & Methodology"):
    st.markdown("""
    ### 📊 Understanding the Metrics

    * **Valuation (P/E):** Compares share price to earnings. 
        * :white_check_mark: *Good Value (<20):* The stock is "on sale" compared to its profits.
        * :warning: *Pricey (>35):* You are paying a high premium for every $1 of profit.

    * **Revenue Multiple (P/S):** Measures price against total sales. 
        * :white_check_mark: *Fair Sales (<2.0):* You are paying a low multiple for the company's revenue.
        * :warning: *High Premium (>5.0):* High growth expectations (common in tech).

    * **Asset Value (P/B):** Compares market price to "book value" (net assets).
        * :gem: *Undervalued (<1.5):* Trading close to physical asset value.
        * :warning: *Asset Heavy (>4.0):* Value is tied more to brand/IP than physical assets.

    * **Efficiency (ROE):** Shows how well management uses equity to make profit.
        * :fire: *High Power (>20%):* Exceptional management and profitability.
        * :snail: *Slow (<10%):* Struggling to generate returns on capital.

    * **Safety (Debt/Equity):** Measures financial risk.
        * :shield: *Very Safe (<0.5):* Very little debt compared to assets.
        * :triangular_flag_on_post: *Risky Debt (>1.5):* Heavily leveraged; sensitive to interest rates.
    """)
        except Exception as e:
            st.error(f"Error processing {ticker_input}: {e}")
