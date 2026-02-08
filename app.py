import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro", page_icon="📈")
st.title("📈 Cicim Bot: Professional Stock Analysis")

# --- 2. DUAL-MODE RATING LOGIC ---
def get_rating(val, metric_type):
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
    st.header("Search & Watchlist")
    
    # Initialize session state for ticker if it doesn't exist
    if 'ticker' not in st.session_state:
        st.session_state.ticker = "TSM"

    ticker_input = st.text_input("Enter Ticker Symbol", value=st.session_state.ticker).upper()
    
    st.write("---")
    st.subheader("Quick Select")
    watchlist = {
        "TSM": "Taiwan Semi",
        "NVDA": "NVIDIA",
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        "META": "Meta"
    }
    
    for symbol, name in watchlist.items():
        if st.button(f"{symbol} ({name})", use_container_width=True):
            st.session_state.ticker = symbol
            st.rerun()
            
    st.write("---")
    run_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)
    st.info("The Modern Score is recommended for Tech and SaaS sectors.")

# --- 4. MAIN APP LOGIC ---
if run_btn or st.session_state.ticker:
    ticker_to_use = st.session_state.ticker if not run_btn else ticker_input
    try:
        stock = yf.Ticker(ticker_to_use)
        info = stock.info

        # 4a. Core Metrics
        pe = info.get('trailingPE')
        ps = info.get('priceToSalesTrailing12Months')
        pb = info.get('priceToBook')
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        debt = (info.get('debtToEquity', 0) or 0) / 100

        # 4b. Safety & Sentiment Metrics (NEW)
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        payout = (info.get('payoutRatio', 0) or 0) * 100
        target = info.get('targetMeanPrice')
        curr_price = info.get('currentPrice', 1)
        upside = ((target / curr_price) - 1) * 100 if target else 0

        # 4c. Scoring
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt

        # --- 5. INTERACTIVE CHART ---
        st.subheader(f"TradingView Interactive: {ticker_to_use}")
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%", "height": 450, "symbol": "{ticker_to_use}",
            "interval": "D", "theme": "light", "style": "1", "locale": "en",
            "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_widget, height=470)

        # --- 6. SAFETY & SENTIMENT (NEW) ---
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Dividend Yield", f"{div_yield:.2f}%")
        col_s2.metric("Payout Ratio", f"{payout:.1f}%", delta="⚠️ Risk" if payout > 75 else "✅ Safe", delta_color="inverse")
        col_s3.metric("Analyst Upside", f"{upside:.1f}%", delta=f"Target: ${target}" if target else "No Data")

        # --- 7. SCOREBOARD ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Classic Score (Includes P/B)", f"{classic_total}/100")
        c2.metric("Modern Score (NO P/B)", f"{modern_total}/100")

        # --- 8. DATA TABLE ---
        df_display = pd.DataFrame({
            "Metric": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity"],
            "Value": [f"{pe:.2f}" if pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{pb:.2f}" if pb else "N/A", f"{roe:.2f}%", f"{debt:.2f}"],
            "Rating": [l_pe, l_ps, l_pb, l_roe, l_debt]
        })
        st.table(df_display)

      # --- 9. NEWS FEED (Fixed for 2026) ---
st.subheader(f"Latest News: {ticker_to_use}")
try:
    news = stock.news
    if not news:
        st.write("No recent news found for this ticker.")
    else:
        # Take only the first 5 news items
        for item in news[:5]:
            # Use .get() to avoid KeyError if 'title' or 'link' is missing
            title = item.get('title', 'Headline Unavailable')
            link = item.get('link', '#')
            publisher = item.get('publisher', 'Unknown Source')
            
            st.write(f"📌 **[{title}]({link})**")
            st.caption(f"Source: {publisher}")
except Exception as news_err:
    st.warning(f"Could not load news feed: {news_err}")

        # --- 10. METHODOLOGY ---
        with st.expander("🚦 Deep Dive: Analytical Framework & Scoring Logic"):
            st.markdown(fr"""
            ### 📜 Methodology Overview
            This tool uses a **Weighted Simple Additive Scoring (WSAS)** model.
            
            #### 1. The Dual-Score Approach
            * **Classic Analysis:** Based on Graham's Value principles. Includes **P/B** (20% weight per metric).
            * **Modern Analysis:** Tailored for the Intangible Era. Excludes **P/B** (25% weight per metric).

            ---

            ### 🧪 The Five Pillars
            1. **P/E Ratio:** Measures valuation vs. profit. Benchmark: < 20 is "Value".
            2. **P/S Ratio:** Valuation vs. Revenue. Critical for growth tech. Benchmark: < 2.0.
            3. **P/B Ratio:** Valuation vs. Assets. Benchmark: 1.0 is "Book Value".
            4. **ROE % (Efficiency):** $ROE = \frac{{\text{{Net Income}}}}{{\text{{Shareholders' Equity}}}}$
               Shows how effectively management reinvests your capital.
            5. **Debt-to-Equity:** Measures leverage. < 0.8 is conservative/safe.
            """)
    except Exception as e:
        st.error(f"Error analyzing {ticker_to_use}: {e}")
