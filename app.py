import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. CACHED DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_finance_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Familio AI", page_icon="📈")
st.title("📈 Familio AI Bot: Multi-Asset Analysis")

def get_rating(val, metric_type):
    if val in ["N/A", None, 0]:
        return "⚪ Neutral", 0
    
    # Valuation / ETF Specifics
    if metric_type in ["PE", "FPE"]:
        if val < 20: return "✅ Good Value", 20
        if val < 40: return "⚖️ Average", 10
        return "⚠️ Pricey", 0
    if metric_type == "ExpenseRatio":
        if val < 0.15: return "🛡️ Ultra Low Cost", 20
        if val < 0.50: return "⚖️ Standard", 10
        return "🚩 Expensive Fee", 0
    
    # Profitability / Efficiency
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0
    if metric_type == "Margin":
        if val > 20: return "💰 High Profit", 20
        if val > 10: return "⚖️ Healthy", 10
        return "Thin", 0
        
    # Health / Liquidity
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0
    if metric_type == "CurrentRatio":
        if val > 1.5: return "💧 Liquid", 20
        if val > 1.0: return "⚖️ Stable", 10
        return "⚠️ Cash Tight", 0

    return "⚪ Neutral", 0

# --- 3. SIDEBAR (STOCK & ETF SEARCH) ---
with st.sidebar:
    st.header("🔍 Search Terminal")
    
    # Toggle for Asset Type
    asset_type = st.radio("Select Asset Class", ["Stocks", "ETFs"])
    
    if asset_type == "Stocks":
        ticker_input = st.text_input("Enter Stock Ticker", "TSM").upper()
    else:
        ticker_input = st.text_input("Enter ETF Ticker", "VOO").upper()
    
    st.write("---")
    st.subheader("Quick Watchlist")
    
    watchlist = {
        "NVDA": "NVIDIA", "VOO": "S&P 500 ETF", "QQQ": "Nasdaq 100", 
        "TSM": "Taiwan Semi", "META": "Meta", "SCHD": "Dividend ETF"
    }
    
    for symbol, name in watchlist.items():
        if st.button(f"{symbol} - {name}", key=f"btn_{symbol}", use_container_width=True):
            ticker_input = symbol 
            
    st.write("---")
    run_btn = st.button("🚀 Run Deep Analysis", type="primary", use_container_width=True)

# --- 4. MAIN APP LOGIC ---
if run_btn or ticker_input:
    try:
        info = fetch_finance_data(ticker_input)

        if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info and 'navPrice' not in info):
            st.error("No data found. Please check the ticker symbol.")
            st.stop()
            
        # Detect Asset Type from Info
        is_etf = info.get('quoteType') == 'ETF'
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice')

        # Unified Metrics
        target = info.get('targetMeanPrice')
        upside = ((target / curr_price) - 1) * 100 if target else 0
        div_yield = (info.get('dividendYield', 0) or 0) * 100

        # Conditional Logic for Scoring & Tables
        if is_etf:
            exp_ratio = info.get('trailingAnnualDividendYield', 0) # Placeholder if info is sparse
            fee = info.get('feesReportedFinancing', 0) or 0.0003 # Default low for VOO/SPY
            l_fee, s_fee = get_rating(fee * 100, "ExpenseRatio")
            total_score = 75 if fee < 0.001 else 60 # ETF scoring simplified
            verdict, color = ("🚀 STRONG BUY", "green") if fee < 0.001 else ("⚖️ HOLD", "gray")
        else:
            # Stock Metrics
            pe = info.get('trailingPE')
            f_pe = info.get('forwardPE') 
            ps = info.get('priceToSalesTrailing12Months')
            pb = info.get('priceToBook')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            profit_margin = (info.get('profitMargins', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            current_ratio = info.get('currentRatio')

            # Scoring
            l_pe, s_pe = get_rating(pe, "PE")
            l_fpe, s_fpe = get_rating(f_pe, "FPE") 
            l_ps, s_ps = get_rating(ps, "PS")
            l_pb, s_pb = get_rating(pb, "PB")
            l_roe, s_roe = get_rating(roe, "ROE")
            l_margin, s_margin = get_rating(profit_margin, "Margin")
            l_debt, s_debt = get_rating(debt, "DEBT")
            l_cr, s_cr = get_rating(current_ratio, "CurrentRatio")

            fundamental_total = (s_pe + s_ps + s_pb + s_roe + s_debt + s_margin + s_cr) / 1.4
            tech_score = 30 if upside > 15 else (15 if upside > 0 else 0)
            total_score = (fundamental_total * 0.7) + tech_score
            
            if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
            elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
            elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
            else: verdict, color = "🚩 SELL", "red"
            
        # --- 5. VISUALS ---
        st.markdown(f"""
            <div style="background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid white;">
                <h1 style="color:white; margin:0;">Verdict: {verdict}</h1>
                <h2 style="color:white; margin:0;">AI Score: {int(total_score)}/100</h2>
            </div>
        """, unsafe_allow_html=True)

        st.subheader(f"Live Analysis: {info.get('longName', ticker_input)}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${curr_price}")
        m2.metric("Asset Type", "ETF" if is_etf else "Equity Stock")
        m3.metric("Div. Yield", f"{div_yield:.2f}%")
        m4.metric("Market Cap/Assets", f"${(info.get('marketCap', info.get('totalAssets', 0))/1e9):.1f}B")

        # TradingView Chart
        tradingview_widget = f"""
        <div class="tradingview-widget-container">
          <div id="tv_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "width": "100%", "height": 450, "symbol": "{ticker_input}",
            "interval": "D", "theme": "light", "style": "1", "locale": "en",
            "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]
          }});
          </script>
        </div>
        """
        components.html(tradingview_widget, height=470)

        # --- CHART ANALYSIS DESCRIPTION ---
        st.markdown("### 📈 How to Read This Chart")
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.info("""
            **Relative Strength Index (RSI):**
            * **Over 70:** The asset is 'Overbought'. It might be due for a price drop or 'cool down.'
            * **Under 30:** The asset is 'Oversold'. This often indicates a potential buying opportunity.
            """)
        with c_col2:
            st.info("""
            **Moving Averages (MA):**
            * **Price Above MA:** Indicates a strong bullish trend (positive momentum).
            * **Price Below MA:** Indicates a bearish trend (negative momentum). 
            """)

        # --- 6. DATA TABLES ---
        st.write("---")
        if is_etf:
            st.write("### 🧺 ETF Structure & Performance")
            st.table(pd.DataFrame({
                "Metric": ["Fund Family", "Category", "Legal Type", "Expense Ratio", "Total Assets"],
                "Value": [info.get('fundFamily'), info.get('category'), info.get('fundInceptionDate'), f"{info.get('trailingAnnualDividendYield', 'N/A')}", f"${(info.get('totalAssets', 0)/1e9):.2f}B"]
            }))
        else:
            st.write("### 📊 Deep Fundamental Audit")
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("#### Valuation & Growth")
                st.table(pd.DataFrame({
                    "Metric": ["Trailing P/E", "Forward P/E", "Price to Sales", "Upside"],
                    "Value": [f"{pe:.2f}" if pe else "N/A", f"{f_pe:.2f}" if f_pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{upside:.1f}%"],
                    "Rating": [l_pe, l_fpe, l_ps, "Sentiment"]
                }))
            with col_right:
                st.markdown("#### Efficiency & Solvency")
                st.table(pd.DataFrame({
                    "Metric": ["ROE", "Profit Margin", "Debt to Equity", "Current Ratio"],
                    "Value": [f"{roe:.2f}%", f"{profit_margin:.2f}%", f"{debt:.2f}", f"{current_ratio:.2f}"],
                    "Rating": [l_roe, l_margin, l_debt, l_cr]
                }))

    except Exception as e:
        st.error(f"Error: {e}")
