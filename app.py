import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro", page_icon="📈")
st.title("📈 Cicim Bot: Professional Stock Analysis")

# --- 2. RATING ENGINE LOGIC ---
def get_rating(val, metric_type):
    """Calculates ratings and points based on quantitative benchmarks."""
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

# --- 3. SIDEBAR (WATCHLIST & SEARCH) ---
with st.sidebar:
    st.header("Search & Watchlist")
    ticker_input = st.text_input("Enter Ticker Symbol", "TSM").upper()
    
    st.write("---")
    st.subheader("Quick Select")
    watchlist = {"TSM": "Taiwan Semi", "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "META": "Meta"}
    for symbol, name in watchlist.items():
        if st.button(f"{symbol} ({name})", use_container_width=True):
            ticker_input = symbol 
            
    st.write("---")
    run_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)

# --- 4. MAIN APP LOGIC ---
if run_btn or ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info

        # 4a. Fundamental Metrics
        pe = info.get('trailingPE')
        ps = info.get('priceToSalesTrailing12Months')
        pb = info.get('priceToBook')
        roe = (info.get('returnOnEquity', 0) or 0) * 100
        debt = (info.get('debtToEquity', 0) or 0) / 100

        # 4b. Safety & Sentiment
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        payout = (info.get('payoutRatio', 0) or 0) * 100
        target = info.get('targetMeanPrice')
        curr_price = info.get('currentPrice', 1)
        upside = ((target / curr_price) - 1) * 100 if target else 0

        # 4c. ESG & Sustainability Extraction
        try:
            sus = stock.sustainability
            if sus is not None and not sus.empty:
                esg_score = sus.loc['totalEsg', 'Value']
                env_score = sus.loc['environmentScore', 'Value']
                soc_score = sus.loc['socialScore', 'Value']
                gov_score = sus.loc['governanceScore', 'Value']
                
                if esg_score < 20: esg_label, esg_color = "🌿 Low Risk", "normal"
                elif esg_score < 35: esg_label, esg_color = "⚖️ Medium Risk", "off"
                else: esg_label, esg_color = "🚩 High Risk", "inverse"
            else:
                esg_score = None
        except:
            esg_score = None

        # 4d. Scoring Calculations
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt

        # --- 5. UI DISPLAY (CHART) ---
        st.subheader(f"Interactive Chart: {ticker_input}")
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%", "height": 400, "symbol": "{ticker_input}",
            "interval": "D", "theme": "light", "style": "1", "locale": "en",
            "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(tradingview_widget, height=420)

        # --- 6. SAFETY & ESG CARDS ---
        st.write("### 🛡️ Safety, Sentiment & ESG")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Dividend Yield", f"{div_yield:.2f}%")
        col_s2.metric("Payout Ratio", f"{payout:.1f}%", delta="⚠️ High" if payout > 75 else "✅ Healthy", delta_color="inverse")
        col_s3.metric("Analyst Upside", f"{upside:.1f}%", delta=f"Target: ${target}" if target else "N/A")

        if esg_score:
            st.divider()
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("ESG Risk Score", f"{esg_score:.1f}", delta=esg_label, delta_color=esg_color)
            e2.metric("Env Risk", f"{env_score:.1f}")
            e3.metric("Social Risk", f"{soc_score:.1f}")
            e4.metric("Gov Risk", f"{gov_score:.1f}")

        # --- 7. SCOREBOARD ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Classic Score (Value Focus)", f"{classic_total}/100")
        c2.metric("Modern Score (Growth Focus)", f"{modern_total}/100")

        df_display = pd.DataFrame({
            "Metric": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity"],
            "Value": [f"{pe:.2f}" if pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{pb:.2f}" if pb else "N/A", f"{roe:.2f}%", f"{debt:.2f}"],
            "Rating": [l_pe, l_ps, l_pb, l_roe, l_debt]
        })
        st.table(df_display)

        # --- 8. NEWS FEED (FIXED) ---
        st.subheader(f"📰 Latest News: {ticker_input}")
        try:
            news = stock.news
            if news:
                for item in news[:5]:
                    title = item.get('title', 'Headline Unavailable')
                    link = item.get('link', '#')
                    st.markdown(f"**[{title}]({link})**")
                    st.caption(f"Source: {item.get('publisher', 'Unknown')}")
            else:
                st.info("No news found.")
        except:
            st.warning("News currently unavailable.")

        # --- 9. METHODOLOGY ---
        with st.expander("🚦 Methodology & ESG Explanation"):
            st.markdown(fr"""
            ### 🔍 Core Fundamental Pillars
            - **P/E Ratio:** Price / Earnings. < 20 is "Value".
            - **ROE:** Efficiency. $ROE = \frac{{\text{{Net Income}}}}{{\text{{Shareholders' Equity}}}}$. > 18% is "High Power".
            - **Debt/Equity:** Risk. < 0.8 is "Safe".
            
            ### 🌍 ESG Sustainability
            - **Scale:** 0–100. **Lower is better** (measures "unmanaged risk").
            - **Leader (< 20):** Company is highly resilient to climate and social risks.
            - **Laggard (> 40):** High risk of fines or governance scandals.
            
            ### 🛡️ Safety Metrics
            - **Payout Ratio:** % of profit paid as dividends. > 75% is a "Danger Zone".
            - **Analyst Upside:** Difference between current price and Wall Street's 12-month target.
            """)
    except Exception as e:
        st.error(f"Error: {e}")
