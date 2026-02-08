import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- NEW: CACHED DATA FETCHING ---
@st.cache_data(ttl=3600)  # Saves data for 1 hour (3600 seconds)
def fetch_stock_data(ticker):
    """Downloads all necessary data once and stores it in cache."""
    stock = yf.Ticker(ticker)
    # We return the .info dictionary directly
    return stock.info

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro", page_icon="📈")
st.title("📈 Familio AI Bot Stock Analysis")

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
        if st.button(f"{symbol} ({name})", key=symbol, use_container_width=True):
            ticker_input = symbol 
            
    st.write("---")
    run_btn = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)
    st.info("The Modern Score is recommended for Tech and SaaS sectors.")

# --- 4. MAIN APP LOGIC ---
if run_btn or ticker_input:
    try:
        # Use the cached function instead of calling yf.Ticker every time
        info = fetch_stock_data(ticker_input)

        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            st.error("No data found. Check the ticker symbol or wait for rate limit reset.")
            st.stop()
            
        # ... rest of your logic (pe = info.get('trailingPE'), etc.)
        
        # 4a. Basic Metrics
        pe = info.get('trailingPE')
        f_pe = info.get('forwardPE') 
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

        # 4c. Scoring Calculation
        l_pe, s20_pe, s25_pe = get_rating(pe, "PE")
        l_fpe, _, _ = get_rating(f_pe, "FPE") 
        l_ps, s20_ps, s25_ps = get_rating(ps, "PS")
        l_pb, s20_pb, _      = get_rating(pb, "PB")
        l_roe, s20_roe, s25_roe = get_rating(roe, "ROE")
        l_debt, s20_debt, s25_debt = get_rating(debt, "DEBT")

        classic_total = s20_pe + s20_ps + s20_pb + s20_roe + s20_debt
        modern_total = s25_pe + s25_ps + s25_roe + s25_debt
        
        fundamental_score = s20_pe + s20_roe + s20_debt + s20_ps + s20_pb
        
        # 4d. Technical Signal Logic
        tech_score = 0
        if upside > 15: tech_score += 30
        elif upside > 0: tech_score += 15
        
        # Final Combined Score
        total_score = (fundamental_score * 0.7) + (tech_score) 
        
        if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
        elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
        elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
        else: verdict, color = "🚩 SELL", "red"
            
        # --- 5.1 DISPLAY VERDICT (FIXED LINE BELOW) ---
        st.markdown(f"""
            <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;">
                <h1 style="color:white; margin:0;">Verdict: {verdict}</h1>
                <h2 style="color:white; margin:0;">Total Score: {int(total_score)}/100</h2>
            </div>
        """, unsafe_allow_html=True)

        # --- 5.2 INTERACTIVE CHART ---
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
            "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies", "BBands@tv-basicstudies"]
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

        # --- 8. DATA TABLE ---
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

        # --- 10. METHODOLOGY ---
        with st.expander("🚦 Full Methodology & Indicator Explanations"):
            st.markdown(fr"""
            ### 📊 The Rating System
            The **Cicim Bot** uses two scoring models to assess a stock's health:
            - **Classic Score (Value):** 20 points each for PE, PS, PB, ROE, Debt.
            - **Modern Score (Growth):** 25 points each, excluding **P/B**.
            
            **Return on Equity (ROE) Formula:**
            $ROE = \frac{{\text{{Net Income}}}}{{\text{{Shareholders' Equity}}}}$
            """)

            # --- 10. FINAL EXPLANATION SECTION ---
        st.divider()
        st.header("📖 Analysis Guide & Methodology")
        
        tab1, tab2, tab3 = st.tabs(["📊 Fundamental Pillars", "📈 Technical Signals", "🤖 The Scoring Engine"])

        with tab1:
            st.markdown("""
            ### The 5 Pillars of Value
            These metrics tell us if the company is a "money-making machine" or a "money pit."
            
            1. **P/E (Trailing & Forward):** The most common valuation tool. 
               * *Trailing* is based on last year; *Forward* is based on analyst predictions. 
               * **Cheap:** < 20 | **Average:** 20-40 | **Expensive:** > 40.
            2. **ROE (Return on Equity):** Measures efficiency. 
               * High ROE (>18%) means management is excellent at turning shareholder cash into profit.
            3. **Debt/Equity:** Financial health. 
               * A ratio < 0.8 means the company owns much more than it owes. High debt (>1.6) is a red flag.
            4. **P/S (Price to Sales):** Measures revenue value. 
               * Essential for growth stocks that don't have consistent profits yet.
            5. **P/B (Price to Book):** The "Liquidation" value. 
               * If the company went bankrupt tomorrow, what are the physical assets worth?
            """)

        with tab2:
            st.markdown("""
            ### Technical Indicators (Chart Analysis)
            These metrics tell us if *now* is a good time to enter the trade.
            
            * **RSI (Relative Strength Index):** * **Overbought (>70):** The stock is "too hot" and might crash soon.
               * **Oversold (<30):** The stock is "on sale" and might bounce up.
            * **EMA (Exponential Moving Average):** * When the **50 EMA** is above the **200 EMA**, the stock is in a "Golden" uptrend.
            * **Analyst Upside:** * This represents the average price target from professional Wall Street analysts compared to the current price.
            """)

        with tab3:
            st.markdown(fr"""
            ### How the "Cicim Verdict" is Calculated
            The bot uses a weighted algorithm to ensure we don't buy a "cheap" stock that is actually dying, or an "expensive" stock that is a rocket ship.
            
            #### 1. The Math
            We calculate a **Fundamental Base (70%)** and add a **Technical Bonus (30%)**.
            
            $$Score = (Fund\_Score \times 0.7) + (Tech\_Score)$$
            
            #### 2. The Logic Gates
            * **Strong Buy (80-100):** Perfect alignment. Great value and a positive chart trend.
            * **Buy (60-79):** Solid fundamentals, though the entry price might not be "perfect."
            * **Hold (40-59):** The stock is "Fairly Valued." Not a bargain, but not a disaster.
            * **Sell (<40):** Either the business is struggling with debt/low ROE, or the price is extremely overextended (bubble territory).
            """)

    except Exception as e:
        st.error(f"Error: {e}")
            
    except Exception as e:
        st.error(f"Error: {e}")
