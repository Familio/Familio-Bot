import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro", page_icon="📈")
st.title("📈 Cicim Bot: Professional Stock Analysis")

def get_rating(val, metric_type):
    """Calculates scores based on standard financial benchmarks."""
    # 1. Handle missing data first
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0, 0
    
    # 2. Handle P/E and Forward P/E (FPE)
    if metric_type in ["PE", "FPE"]:
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

    # 2.1 Safety Fallback (Prevents the Unpacking Error)
    return "⚪ Neutral", 0, 0

# --- 3. SIDEBAR (WATCHLIST & SEARCH) ---
with st.sidebar:
    st.header("Search & Watchlist")
    
    # Text input for manual search
    ticker_input = st.text_input("Enter Ticker Symbol", "TSM").upper()
    
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
    
    # If a button is clicked, we update the search box indirectly
    for symbol, name in watchlist.items():
        if st.button(f"{symbol} ({name})", use_container_width=True):
            ticker_input = symbol 
            
    st.write("---")
    run_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)
    st.info("The Modern Score is recommended for Tech and SaaS sectors.")

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

         # 4b. Safety & Sentiment (NEW OVERVIEW METRICS)
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        payout = (info.get('payoutRatio', 0) or 0) * 100
        target = info.get('targetMeanPrice')
        curr_price = info.get('currentPrice', 1)
        upside = ((target / curr_price) - 1) * 100 if target else 0

        # 4c. Scoring Calculation
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_fpe, _, _ = get_rating(f_pe, "FPE") # Added for table display
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt

         # 4b. Fundamental Scoring
        l_pe, s20_pe, _ = get_rating(pe, "PE")
        l_fpe, _, _ = get_rating(f_pe, "FPE")
        l_roe, s20_roe, _ = get_rating(roe, "ROE")
        l_debt, s20_debt, _ = get_rating(debt, "DEBT")
        l_ps, s20_ps, _ = get_rating(ps, "PS")
        l_pb, s20_pb, _ = get_rating(pb, "PB")
        
        fundamental_score = s20_pe + s20_roe + s20_debt + s20_ps + s20_pb
        
        # 4c. Technical Signals (Quick Approximation)
        upside = ((target / curr_price) - 1) * 100 if target else 0
        tech_score = 0
        if upside > 15: tech_score += 30
        elif upside > 0: tech_score += 15
        
        # Final Combined Score
        total_score = (fundamental_score * 0.7) + (tech_score) # Weighted 70/30
        
        if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
        elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
        elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
        else: verdict, color = "🚩 SELL", "red"
            
# --- 5.1 DISPLAY VERDICT ---
        st.markdown(f"""
            <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;">
                <h1 style="color:white; margin:0;">Verdict: {verdict}</h1>
                <h2 style="color:white; margin:0;">Total Score: {int(total_score)}/100</h2>
            </div>
        """, unsafe_content_html=True)

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

         # --- 6. SAFETY & SENTIMENT METRICS ---
        st.write("### 🛡️ Safety & Sentiment Overview")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Dividend Yield", f"{div_yield:.2f}%")
        col_s2.metric("Payout Ratio", f"{payout:.1f}%", 
                    delta="⚠️ High Risk" if payout > 75 else "✅ Healthy", delta_color="inverse")
        col_s3.metric("Analyst Upside", f"{upside:.1f}%", 
                    delta=f"Target: ${target}" if target else "No Data")

        # --- 7. SCOREBOARD ---
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Classic Score (Includes P/B)", f"{classic_total}/100")
        c2.metric("Modern Score (NO P/B)", f"{modern_total}/100")

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
            ### 📊 The Rating System
            The **Cicim Bot** uses two scoring models to assess a stock's health:
            - **Classic Score (Value):** Assigns **20 points** to each of the 5 pillars (PE, PS, PB, ROE, Debt). Ideal for manufacturing and banking.
            - **Modern Score (Growth):** Assigns **25 points** to 4 pillars, excluding **Price-to-Book (P/B)**. Preferred for software and AI companies where physical assets are less relevant.

            ---

            ### 🔍 Indicator Explanations
            
            #### 1. Price-to-Earnings (P/E) Ratio
            * **Definition:** Compares stock price to earnings per share (EPS). It shows how many dollars investors pay for each dollar of profit.
            * **Rating:**
                * **✅ Good Value (< 20):** Often indicates undervaluation or a bargain price.
                * **⚖️ Average (20–40):** Fairly priced for moderate growth.
                * **⚠️ Pricey (> 40):** High expectations; risk of being overvalued.

            #### 2. Price-to-Sales (P/S) Ratio
            * **Definition:** Compares market cap to total revenue. Critical for growing companies that aren't profitable yet.
            * **Rating:**
                * **✅ Fair Sales (< 2.0):** Generally considered a healthy, low valuation.
                * **⚠️ High Premium (> 5.0):** Investors are paying a massive premium for revenue.

            #### 3. Price-to-Book (P/B) Ratio
            * **Definition:** Compares stock price to the "book value" (assets minus liabilities).
            * **Rating:**
                * **💎 Undervalued (< 1.5):** Trading close to its liquidation value.
                * **⚠️ Asset Heavy (> 4.0):** High valuation relative to physical assets.

            #### 4. Return on Equity (ROE)
            * **Formula:** $ROE = \frac{{\text{{Net Income}}}}{{\text{{Shareholders' Equity}}}}$
            * **Definition:** Measures how efficiently management generates profit using shareholder capital.
            * **Rating:**
                * **🔥 High Power (> 18%):** Exceptional management efficiency.
                * **🐌 Slow (< 8%):** Management is struggling to grow investor money.

            #### 5. Debt-to-Equity (D/E)
            * **Definition:** Measures financial leverage and risk. High ratios mean the company relies heavily on borrowed money.
            * **Rating:**
                * **🛡️ Very Safe (< 0.8):** Conservative balance sheet; low risk of bankruptcy.
                * **🚩 Risky Debt (> 1.6):** High leverage; vulnerable during economic downturns.
          ---

                ### 🛡️ Safety & Sentiment Methodology

            #### 1. Dividend Yield
            - **Formula:** $\text{{Annual Div per Share}} / \text{{Stock Price}}$
            - **Explanation:** Measures the cash return you get just for owning the stock.
            - **Rating Philosophy:** - **2% - 4%:** Usually the "Sweet Spot" for stable growth + income.
                - **> 6%:** **Red Flag Warning.** Often indicates a "Yield Trap" where the stock price has crashed due to fundamental trouble, making the yield look artificially high.

            #### 2. Payout Ratio
            - **Formula:** $\text{{Total Dividends}} / \text{{Net Income}}$
            - **Explanation:** The percentage of earnings a company pays out as dividends.
            - **Rating Philosophy:**
                - **< 50%:** **Excellent.** Plenty of room to grow dividends and reinvest in the business.
                - **50% - 75%:** **Healthy.** Common for mature companies (Utilities, Staples).
                - **> 75%:** **Danger.** If earnings drop slightly, the company may be forced to cut the dividend to save cash.

            #### 3. Analyst Upside (Price Targets)
            - **Formula:** $(\text{{Average Target Price}} / \text{{Current Price}}) - 1$
            - **Explanation:** The consensus of Wall Street experts on where the stock will be in 12 months.
            - **Rating Philosophy:** - **Positive Upside:** Market sentiment suggests the stock is currently undervalued.
                - **Negative Upside:** The stock may have "run too hot" and is trading above what analysts believe is its fair value.
            """)
            
    except Exception as e:
        st.error(f"Error: {e}")
