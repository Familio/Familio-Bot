import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro", page_icon="📈")
st.title("📈 Cicim Bot: Professional Stock Analysis")

# --- 2. DUAL-MODE RATING LOGIC ---
def get_rating(val, metric_type):
    """Calculates scores based on standard financial benchmarks."""
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0, 0
    
    if metric_type in ["PE", "FPE"]: # P/E and Forward P/E share similar logic
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
    st.header("Search & Watchlist")
    ticker_input = st.text_input("Enter Ticker Symbol", "TSM").upper()
    st.write("---")
    run_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)

# --- 4. MAIN APP LOGIC ---
if run_btn or ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info

        # 4a. Basic Metrics (Added Forward PE)
        pe = info.get('trailingPE')
        f_pe = info.get('forwardPE') # <-- NEW INDICATOR
        ps = info.get('priceToSalesTrailing12Months')
        pb = info.get('priceToBook')
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        debt = (info.get('debtToEquity', 0) or 0) / 100

        # 4b. Scoring Calculation
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_fpe, _, _ = get_rating(f_pe, "FPE") # Added for table display
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt

        # --- 5. INTERACTIVE CHART (WITH TECHNICAL INDICATORS) ---
        st.subheader(f"Interactive Chart: {ticker_input}")
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%", "height": 500, "symbol": "{ticker_input}",
            "interval": "D", "theme": "light", "style": "1", "locale": "en",
            "container_id": "tradingview_chart",
            "studies": [
              "RSI@tv-basicstudies",
              "MASimple@tv-basicstudies",
              "BBands@tv-basicstudies"
            ]
          }});
          </script>
        </div>
        """
        components.html(tradingview_widget, height=520)

        # --- 8. DATA TABLE (Updated with Forward P/E) ---
        st.write("### 📊 Fundamental Metrics")
        df_display = pd.DataFrame({
            "Metric": ["P/E (Trailing)", "Forward P/E", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity"],
            "Value": [
                f"{pe:.2f}" if pe else "N/A", 
                f"{f_pe:.2f}" if f_pe else "N/A", 
                f"{ps:.2f}" if ps else "N/A", 
                f"{pb:.2f}" if pb else "N/A", 
                f"{roe:.2f}%", 
                f"{debt:.2f}"
            ],
            "Rating": [l_pe, l_fpe, l_ps, l_pb, l_roe, l_debt]
        })
        st.table(df_display)

        # --- 10. EXPANDED METHODOLOGY ---
        with st.expander("🚦 Full Methodology & Indicator Explanations"):
            st.markdown(fr"""
            #### 🆕 Forward P/E Ratio (Added)
            * **Definition:** Similar to P/E, but uses **estimated future earnings** for the next 12 months.
            * **Why it matters:** If the Forward P/E is **lower** than the Trailing P/E, analysts expect the company's profits to grow.
            """)
            
    except Exception as e:
        st.error(f"Error: {e}")
