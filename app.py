import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

# --- 2. RATING LOGIC ---
def get_rating(val, metric_type):
    """Calculates status and points for the overall score (20 pts each)"""
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
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
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
            trailing_pe = info.get('trailingPE') # This is P/E TTM
            f_pe = info.get('forwardPE')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            ps_ratio = info.get('priceToSalesTrailing12Months')
            pb_ratio = info.get('priceToBook')
            cap_str = f"${mkt_cap/1e12:.2f}T" if mkt_cap >= 1e12 else f"${mkt_cap/1e9:.2f}B"

            # 4b. Calculate Individual & Total Scores
            # Rating logic uses Trailing P/E as primary
            pe_label, pe_score = get_rating(trailing_pe, "PE")
            roe_label, roe_score = get_rating(roe, "ROE")
            debt_label, debt_score = get_rating(debt, "DEBT")
            ps_label, ps_score = get_rating(ps_ratio, "PS")
            pb_label, pb_score = get_rating(pb_ratio, "PB")
            
            total_score = pe_score + roe_score + debt_score + ps_score + pb_score
            
            if total_score >= 80: total_status = "💎 Strong Buy Candidate"
            elif total_score >= 50: total_status = "⚖️ Average / Hold"
            else: total_status = "🚩 High Risk / Avoid"

            # --- 5. VISUALS ---
            st.subheader(f"Price Action: {ticker_input}")
            fig = go.Figure(data=[go.Candlestick(
                x=hist.index,
                open=hist['Open'], high=hist['High'],
                low=hist['Low'], close=hist['Close']
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # --- 6. DATA TABLE ---
            st.divider()
            st.subheader("Fundamental Scorecard")
            
            full_data = {
                "Metric": ["P/E (TTM)", "P/E (Forward)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity", "OVERALL SCORE"],
                "Value": [
                    f"{trailing_pe:.2f}" if trailing_pe else "N/A",
                    f"{f_pe:.2f}" if f_pe else "N/A", 
                    f"{ps_ratio:.2f}" if ps_ratio else "N/A",
                    f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                    f"{roe:.2f}%", 
                    f"{debt:.2f}", 
                    f"{total_score}/100"
                ],
                "Status": [pe_label, "Estimate", ps_label, pb_label, roe_label, debt_label, total_status]
            }
            
            df_display = pd.DataFrame(full_data).astype(str)
            st.table(df_display)

         # --- 7. DETAILED METHODOLOGY EXPANDER ---
            st.divider()
            with st.expander("🚦 Deep Dive: Scoring Methodology & Indicators"):
                st.markdown(f"""
                ### How the {total_score}/100 Score is Calculated
                Each of the 5 key metrics below contributes up to **20 points**.
                
                | Indicator | ✅ 20 Points | ⚖️ 10 Points | ⚠️ 0 Points |
                | :--- | :--- | :--- | :--- |
                | **P/E Ratio** | < 20 (Value) | 20 - 40 (Fair) | > 40 (Pricey) |
                | **P/S Ratio** | < 2.0 (Healthy) | 2.0 - 5.0 (Moderate) | > 5.0 (Hype) |
                | **P/B Ratio** | < 1.5 (Asset Safe) | 1.5 - 4.0 (Fair) | > 4.0 (Premium) |
                | **ROE %** | > 18% (Efficient) | 8% - 18% (Average) | < 8% (Slow) |
                | **Debt/Equity**| < 0.8 (Low Risk) | 0.8 - 1.6 (Average) | > 1.6 (Risky) |

                ---

                ### 🔍 Indicator Explanations
                
                * **P/E (Price-to-Earnings):** Measures cost per $1 of profit. **TTM** (Trailing Twelve Months) uses real past data, while **Forward** uses analyst estimates.
                * **P/S (Price-to-Sales):** Compares stock price to total revenue. Revenue is harder to "fake" than profit, making this a very strong growth indicator.
                * **P/B (Price-to-Book):** Compares market value to the company's net assets. A low P/B suggests you are buying the physical business at a bargain.
                * **ROE (Return on Equity):** The "Management Quality" metric. It shows how much profit the company makes with shareholder money.
                * **Debt-to-Equity:** Measures financial leverage. High debt can be dangerous if interest rates rise or sales slow down.

                **Final Verdict Logic:**
                * **80+ points:** 💎 High stability and valuation.
                * **50-70 points:** ⚖️ Solid but has one or two weak spots.
                * **Below 50:** 🚩 Significant valuation or debt concerns.
                """)

    except Exception as e:
        st.error(f"Error processing {ticker_input}: {e}")
