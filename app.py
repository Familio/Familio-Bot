import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Dual-Score Analysis")

# --- 2. DUAL-MODE RATING LOGIC ---
def get_rating(val, metric_type):
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0, 0
    
    # We return: Label, 20-pt score (Classic), 25-pt score (Modern)
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 20, 25
        if val < 40: return "⚖️ Average", 10, 12
        return "⚠️ Pricey", 0, 0
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20, 25
        if val > 8: return "⚖️ Average", 10, 12
        return "🐌 Slow", 0, 0
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20, 25
        if val < 1.6: return "⚖️ Average", 10, 12
        return "🚩 Risky Debt", 0, 0
    if metric_type == "PS":
        if val < 2.0: return "✅ Fair Sales", 20, 25
        if val < 5.0: return "⚖️ Moderate", 10, 12
        return "⚠️ High Premium", 0, 0
    if metric_type == "PB":
        # P/B only exists in the 20-pt (Classic) world
        if val < 1.5: return "💎 Undervalued", 20, 0
        if val < 4.0: return "⚖️ Fair Assets", 10, 0
        return "⚠️ Asset Heavy", 0, 0

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Control Panel")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Dual Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="6mo")

        if hist.empty:
            st.error("Could not find data for this symbol.")
        else:
            # 4a. Data Extraction
            pe_val = info.get('trailingPE')
            roe_val = (info.get('returnOnEquity', 0) or 0) * 100
            debt_val = (info.get('debtToEquity', 0) or 0) / 100
            ps_val = info.get('priceToSalesTrailing12Months')
            pb_val = info.get('priceToBook')

            # 4b. Scoring (Calculating both systems at once)
            l_pe, s20_pe, s25_pe = get_rating(pe_val, "PE")
            l_roe, s20_roe, s25_roe = get_rating(roe_val, "ROE")
            l_debt, s20_debt, s25_debt = get_rating(debt_val, "DEBT")
            l_ps, s20_ps, s25_ps = get_rating(ps_val, "PS")
            l_pb, s20_pb, _ = get_rating(pb_val, "PB") # P/B has no 25-pt score

            classic_total = s20_pe + s20_roe + s20_debt + s20_ps + s20_pb
            modern_total = s25_pe + s25_roe + s25_debt + s25_ps

            # --- 5. TOP METRICS DASHBOARD ---
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Classic Score (with P/B)", f"{classic_total}/100", help="Standard value investing (20pts each)")
            with col2:
                st.metric("Modern Score (NO P/B)", f"{modern_total}/100", help="Tech-focused (25pts each, skips P/B)")

            # --- 6. DATA TABLE ---
            st.subheader("Comparison Table")
            df_data = {
                "Metric": ["P/E (TTM)", "P/S Ratio", "ROE %", "Debt/Equity", "P/B Ratio"],
                "Value": [f"{pe_val:.2f}", f"{ps_val:.2f}", f"{roe_val:.2f}%", f"{debt_val:.2f}", f"{pb_val:.2f}"],
                "Health Status": [l_pe, l_ps, l_roe, l_debt, l_pb]
            }
            st.table(pd.DataFrame(df_data))

            # --- 7. METHODOLOGY ---
            st.divider()
            with st.expander("🚦 How to read these two scores"):
                st.markdown(f"""
                ### 1. Classic Score ({classic_total}/100)
                * Uses all 5 metrics equally (20 points each).
                * **Best for:** Banks, Manufacturing, and Retail.
                
                ### 2. Modern Score ({modern_total}/100)
                * Skips the **P/B Ratio** entirely.
                * Redistributes those points so P/E, P/S, ROE, and Debt are worth **25 points** each.
                * **Best for:** Software, Semiconductors (like TSM), and AI companies.
    

    # --- 7. DETAILED METHODOLOGY EXPANDER ---
st.divider()
with st.expander("🚦 Deep Dive: Scoring Methodology & Indicators"):
    st.markdown(f"""
    ### 🏆 Dual-Score System Explained
    The bot calculates two separate scores using the **Simple Additive Weighting (SAW)** method to give you a complete picture of the company's health.

    #### 1. Classic Score ({classic_total}/100)
    This is the traditional "Value Investing" approach. It assumes physical assets are just as important as earnings and sales.
    * **Weighting:** 5 Indicators × **20 Points** each.
    * **Best for:** Banking, Real Estate, and heavy Manufacturing.

    #### 2. Modern Score ({modern_total}/100)
    This is the "Growth/Tech" approach. It ignores the **P/B Ratio** because high-tech companies' primary assets (IP, talent, and code) aren't accurately captured on a balance sheet.
    * **Weighting:** 4 Indicators × **25 Points** each (P/B is excluded).
    * **Best for:** Software (SaaS), Semiconductors (e.g., TSM), and AI firms.

    ---

    ### 📊 Scoring Thresholds
    | Indicator | ✅ High Points (Best) | ⚖️ Mid Points (Fair) | ⚠️ 0 Points (Poor) |
    | :--- | :--- | :--- | :--- |
    | **P/E Ratio** | < 20 | 20 - 40 | > 40 |
    | **P/S Ratio** | < 2.0 | 2.0 - 5.0 | > 5.0 |
    | **P/B Ratio** | < 1.5 | 1.5 - 4.0 | > 4.0 |
    | **ROE %** | > 18% | 8% - 18% | < 8% |
    | **Debt/Equity**| < 0.8 | 0.8 - 1.6 | > 1.6 |

    ---

    ### 🔍 Indicator Logic in the Code
    1. **P/E (Price-to-Earnings):** We use **TTM (Trailing Twelve Months)** earnings. It tells you how many years of profit it takes to pay back the share price.
    2. **P/S (Price-to-Sales):** Critical for growth companies. It measures valuation relative to total revenue.
    3. **P/B (Price-to-Book):** Measures the stock price against the net "accounting value" of the company.
    4. **ROE (Return on Equity):** Calculated as: $$\\text{{ROE}} = \\frac{{\\text{{Net Income}}}}{{\\text{{Shareholder Equity}}}}$$ It shows how efficiently management generates profit from your investment.
    5. **Debt-to-Equity:** A safety check. A ratio of 1.0 means the company has equal amounts of debt and equity.

    **Verdict Tiers:**
    * **80-100:** 💎 **Strong Buy Candidate** - Peak efficiency and value.
    * **50-70:** ⚖️ **Hold / Average** - Good fundamentals but potentially pricey.
    * **Below 50:** 🚩 **High Risk** - Poor financial health or extreme market "hype."
    """)


    except Exception as e:
        st.error(f"Error: {e}")
