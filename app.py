import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro: Advanced Analysis")
st.title("📈 Cicim Bot: Professional Stock Analysis")

# --- 2. DUAL-MODE RATING LOGIC ---
def get_rating(val, metric_type):
    """
    Returns: (Label, Score_Out_Of_20, Score_Out_Of_25)
    Logic: Scoring is based on historical S&P 500 averages and value investing principles.
    """
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0, 0
    
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
        if val < 1.5: return "💎 Undervalued", 20, 0
        if val < 4.0: return "⚖️ Fair Assets", 10, 0
        return "⚠️ Asset Heavy", 0, 0

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Search")
    ticker_input = st.text_input("Enter Ticker Symbol", "TSM").upper()
    run_btn = st.button("🚀 Analyze Stock")
    st.info("The Modern Score is recommended for Tech and SaaS sectors.")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info

        # 4a. Metrics Extraction
        pe = info.get('trailingPE')
        ps = info.get('priceToSalesTrailing12Months')
        pb = info.get('priceToBook')
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        debt = (info.get('debtToEquity', 0) or 0) / 100

        # 4b. Multi-System Scoring
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt

        # --- 5. INTERACTIVE CHART ---
        st.subheader(f"TradingView Interactive: {ticker_input}")
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%", "height": 500, "symbol": "{ticker_input}",
            "interval": "D", "theme": "light", "style": "1", "locale": "en",
            "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_widget, height=520)

        # --- 6. SCOREBOARD ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Classic Score (Includes P/B)", f"{classic_total}/100")
        c2.metric("Modern Score (NO P/B)", f"{modern_total}/100")

        # --- 7. DATA TABLE ---
        df_display = pd.DataFrame({
            "Metric": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity"],
            "Value": [f"{pe:.2f}" if pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{pb:.2f}" if pb else "N/A", f"{roe:.2f}%", f"{debt:.2f}"],
            "Rating": [l_pe, l_ps, l_pb, l_roe, l_debt]
        })
        st.table(df_display)

        # --- 8. DETAILED METHODOLOGY EXPANDER ---
        with st.expander("🚦 Deep Dive: Analytical Framework & Scoring Logic"):
            st.markdown(f"""
            ### 📜 Methodology Overview
            This tool applies a **Weighted Simple Additive Scoring (WSAS)** model to evaluate fundamental health. It converts complex financial ratios into a standardized 100-point scale.
            
            #### 1. The Dual-Score Approach
            * **Classic Analysis (20% weight per metric):** Based on Benjamin Graham’s "Value" principles. It includes the **Price-to-Book (P/B)** ratio, assuming that a company's physical assets provide a safety net for shareholders.
            * **Modern Analysis (25% weight per metric):** Tailored for the "Intangible Era." It excludes **P/B** because software, patents, and brand power—often the most valuable assets of tech companies like TSM—are frequently undervalued or missing on traditional balance sheets.

            ---

            ### 🧪 The Five Pillars of Analysis
            
            
            1.  **P/E Ratio (Valuation vs. Profit):**
                * *Logic:* Measures how much investors pay for $1 of annual profit.
                * *Benchmark:* < 20 is historically considered "Value," while > 40 suggests high growth expectations or "Bubble" pricing.
            
            2.  **P/S Ratio (Valuation vs. Revenue):**
                * *Logic:* Essential for companies that are reinvesting all profits into growth.
                * *Benchmark:* < 2.0 is highly efficient. > 5.0 indicates you are paying a massive premium for every dollar of sales.

            3.  **P/B Ratio (Valuation vs. Assets):**
                * *Logic:* Calculates the "Liquidation Value."
                * *Benchmark:* A ratio of 1.0 means you are buying the company for exactly what its assets are worth on paper.

            4.  **ROE % (Operational Efficiency):**
                * *Formula:* $ROE = \\frac{\\text{Net Income}}{\\text{Shareholders' Equity}}$
                * *Logic:* Shows how much profit management generates with the money shareholders have invested. An ROE > 18% indicates a "Moat" or strong competitive advantage.

            5.  **Debt-to-Equity (Financial Risk):**
                * *Logic:* Measures leverage. A score of 1.0 means the company has $1 of debt for every $1 of equity. 
                * *Benchmark:* < 0.8 is conservative and safe. > 1.6 indicates high risk of bankruptcy during economic downturns.

            ---

            ### 📊 Verdict Tiers
            * **80 - 100:** 💎 **Strong Fundamental Strength.** High probability of being a "Quality" or "Compounder" stock.
            * **50 - 75:** ⚖️ **Fair / Hold.** Good business, but either slightly expensive or carrying moderate risk.
            * **Below 50:** 🚩 **Speculative / High Risk.** Significant fundamental flaws or extreme overvaluation.
            """)
    except Exception as e:
        st.error(f"Error analyzing {ticker_input}: {e}")
