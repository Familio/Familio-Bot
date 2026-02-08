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
    watchlist = {"TSM": "TSM", "NVDA": "NVDA", "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL", "META": "META"}
    for symbol, name in watchlist.items():
        if st.button(f"🔍 {symbol}", use_container_width=True):
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

        # 4c. ESG & Sustainability
        try:
            sus = stock.sustainability
            if sus is not None and not sus.empty:
                esg_score = sus.loc['totalEsg', 'Value']
                env_score = sus.loc['environmentScore', 'Value']
                soc_score = sus.loc['socialScore', 'Value']
                gov_score = sus.loc['governanceScore', 'Value']
                
                if esg_score < 20: esg_label = "🌿 Low Risk"
                elif esg_score < 35: esg_label = "⚖️ Medium Risk"
                else: esg_label = "🚩 High Risk"
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

        # --- 6. SAFETY & SENTIMENT CARDS ---
        st.write("### 🛡️ Safety & Sentiment")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Dividend Yield", f"{div_yield:.2f}%")
        col_s2.metric("Payout Ratio", f"{payout:.1f}%", 
                    delta="⚠️ High" if payout > 75 else "✅ Healthy", delta_color="inverse")
        col_s3.metric("Analyst Upside", f"{upside:.1f}%", 
                    delta=f"Target: ${target}" if target else "N/A")

        # --- 7. SCOREBOARD ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Classic Score (Value Focus)", f"{classic_total}/100")
        c2.metric("Modern Score (Growth Focus)", f"{modern_total}/100")

        # --- 8. THE COMPLETE DATA TABLE (With ESG) ---
        st.write("### 📊 Comprehensive Report")
        table_data = [
            ["P/E (TTM)", f"{pe:.2f}" if pe else "N/A", l_pe],
            ["P/S Ratio", f"{ps:.2f}" if ps else "N/A", l_ps],
            ["P/B Ratio", f"{pb:.2f}" if pb else "N/A", l_pb],
            ["ROE %", f"{roe:.2f}%", l_roe],
            ["Debt/Equity", f"{debt:.2f}", l_debt]
        ]

        if esg_score:
            table_data.append(["Total ESG Risk", f"{esg_score:.1f}", esg_label])
            table_data.append(["Env Risk Score", f"{env_score:.1f}", "Environmental"])
            table_data.append(["Social Risk Score", f"{soc_score:.1f}", "Social"])
            table_data.append(["Gov Risk Score", f"{gov_score:.1f}", "Governance"])

        df_display = pd.DataFrame(table_data, columns=["Metric", "Value", "Verdict"])
        
        # Applying row coloring logic
        def style_verdict(row):
            if "Good" in str(row.Verdict) or "Safe" in str(row.Verdict) or "Low Risk" in str(row.Verdict) or "Power" in str(row.Verdict):
                return ['background-color: rgba(0, 255, 0, 0.1)'] * len(row)
            if "Risky" in str(row.Verdict) or "Pricey" in str(row.Verdict) or "High Risk" in str(row.Verdict):
                return ['background-color: rgba(255, 0, 0, 0.1)'] * len(row)
            return [''] * len(row)

        st.dataframe(df_display.style.apply(style_verdict, axis=1), width=1000)

        # --- 9. METHODOLOGY ---
        with st.expander("🚦 Methodology, Indicators & ESG Explanation"):
            st.markdown(fr"""
            ### 📜 Scoring Framework
            - **Classic Score:** Uses 5 metrics (PE, PS, PB, ROE, Debt) at 20 points each.
            - **Modern Score:** Uses 4 metrics (PE, PS, ROE, Debt) at 25 points each.
            
            ### 🔍 Pillar Definitions
            1. **P/E Ratio:** Price vs Profit. < 20 is a bargain.
            2. **ROE:** Management efficiency. $ROE = \frac{{\text{{Net Income}}}}{{\text{{Shareholders' Equity}}}}$.
            3. **ESG Risk:** Measures unmanaged risk from 0-100. **Lower is Better**.
            
            ### 🛡️ Safety Thresholds
            - **Payout Ratio:** > 75% means the dividend is at risk of being cut.
            - **D/E Ratio:** > 1.6 indicates a company is heavily reliant on debt.
            """)
    except Exception as e:
        st.error(f"Error: {e}")
