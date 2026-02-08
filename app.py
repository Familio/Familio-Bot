import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro: Yahoo Edition")
st.title("📈 Cicim Bot: Professional Dual-Score Analysis")

# --- 2. DUAL-MODE RATING LOGIC ---
def get_rating(val, metric_type):
    """Returns: (Label, Score_Out_Of_20, Score_Out_Of_25)"""
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

# --- 4. MAIN APP LOGIC ---
if run_btn:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info

        # 4a. Metrics Extraction
        sector = info.get('sector', 'N/A')
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

        # --- 5. VISUAL INTERACTIVE CHART (Yahoo/TradingView Style) ---
        st.subheader(f"Interactive Chart: {ticker_input}")
        
        # HTML/JS for TradingView Widget
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%",
            "height": 500,
            "symbol": "{ticker_input}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
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
        c2.metric("Modern Score (Excludes P/B)", f"{modern_total}/100")

        # --- 7. DATA TABLE ---
        df_display = pd.DataFrame({
            "Indicator": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity"],
            "Current Value": [f"{pe:.2f}" if pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{pb:.2f}" if pb else "N/A", f"{roe:.2f}%", f"{debt:.2f}"],
            "Health Status": [l_pe, l_ps, l_pb, l_roe, l_debt]
        })
        st.table(df_display)

        # --- 8. DETAILED METHODOLOGY ---
        with st.expander("🚦 Deep Dive: Scoring Methodology & Indicators"):
            st.markdown(f"""
            ### 🏆 Dual-Score System
            1. **Classic Score ({classic_total}/100):** Uses all 5 metrics equally (**20 pts each**).
            2. **Modern Score ({modern_total}/100):** Skips **P/B Ratio**. Remaining 4 metrics are worth **25 pts each**.
            
            | Indicator | ✅ High Points | ⚖️ Mid Points | ⚠️ 0 Points |
            | :--- | :--- | :--- | :--- |
            | **P/E Ratio** | < 20 | 20 - 40 | > 40 |
            | **P/S Ratio** | < 2.0 | 2.0 - 5.0 | > 5.0 |
            | **P/B Ratio** | < 1.5 | 1.5 - 4.0 | > 4.0 |
            | **ROE %** | > 18% | 8% - 18% | < 8% |
            | **Debt/Equity**| < 0.8 | 0.8 - 1.6 | > 1.6 |
            """)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
