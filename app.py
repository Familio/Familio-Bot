import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai

# --- 1. PAGE CONFIGURATION ---
st.set_set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

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

                # --- 7. AI VERDICT ---
                with st.spinner("AI analyzing all metrics..."):
                    client = genai.Client(api_key=api_key)
                    prompt = (f"Analyze {ticker_input}. P/E: {f_pe}, P/S: {ps_ratio}, P/B: {pb_ratio}, "
                             f"ROE: {roe}%, Debt/Equity: {debt}. Total Score: {total_score}/100. "
                             "Provide a brief, professional investment summary.")
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    st.info("🤖 AI Executive Verdict")
                    st.write(response.text)

                # --- 8. METHODOLOGY ---
                with st.expander("🚦 Methodology Breakdown"):
                    st.markdown("""
                    Each metric contributes up to **20 points**:
                    * **P/E < 20:** Good value.
                    * **P/S < 2:** Healthy revenue multiple.
                    * **P/B < 1.5:** Trading close to asset value.
                    * **ROE > 18%:** Highly efficient management.
                    * **Debt/Equity < 0.8:** Low financial risk.
                    """)

        except Exception as e:
            st.error(f"Error processing {ticker_input}: {e}")
