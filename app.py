import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components
import plotly.express as px

# --- 1. CACHED DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_finance_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Familio AI", page_icon="📈")
st.title("📈 Familio AI Bot: Advanced Asset Analysis")

def get_rating(val, metric_type):
    """Calculates scores based on standard financial benchmarks."""
    if val in ["N/A", None, 0]:
        return "⚪ Neutral", 0
    
    # Valuation Ratings
    if metric_type in ["PE", "FPE"]:
        if val < 20: return "✅ Good Value", 20
        if val < 40: return "⚖️ Average", 10
        return "⚠️ Pricey", 0
    if metric_type == "PS":
        if val < 2.0: return "✅ Fair Sales", 20
        if val < 5.0: return "⚖️ Moderate", 10
        return "⚠️ High Premium", 0
    if metric_type == "PB":
        if val < 1.5: return "💎 Undervalued", 20
        if val < 4.0: return "⚖️ Fair Assets", 10
        return "⚠️ Asset Heavy", 0
        
    # Profitability/Efficiency Ratings
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0
    if metric_type == "Margin":
        if val > 20: return "💰 High Profit", 20
        if val > 10: return "⚖️ Healthy", 10
        return "Thin", 0
        
    # Health/Debt Ratings
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0
    if metric_type == "CurrentRatio":
        if val > 1.5: return "💧 Liquid", 20
        if val > 1.0: return "⚖️ Stable", 10
        return "⚠️ Cash Tight", 0

    return "⚪ Neutral", 0

# --- 3. SIDEBAR (WATCHLIST & SEARCH) ---
with st.sidebar:
    st.header("Search & Watchlist")
    asset_type = st.radio("Select Asset Class", ["Stocks", "ETFs"])
    
    if asset_type == "Stocks":
        ticker_input = st.text_input("Enter Stock Ticker", "TSM").upper()
        watchlist = {
            "COIN": "Coinbase", "META": "Meta", "MSFT": "Microsoft", 
            "AMZN": "Amazon", "GOOGL": "Alphabet", "TSLA": "Tesla", 
            "PYPL": "Paypal", "HOOD": "Robinhood", "LLY": "Eli Lilly", "TSM": "Taiwan Semi"
        }
    else:
        ticker_input = st.text_input("Enter ETF Ticker", "VOO").upper()
        watchlist = {
            "VOO": "S&P 500", "QQQ": "Nasdaq 100", "SCHD": "Dividend", 
            "VTI": "Total Market", "VGT": "Tech Fund", "XLV": "Health", 
            "XLF": "Financials", "IWM": "Small Cap", "VEA": "Intl Dev", "BND": "Bonds"
        }
    
    st.write("---")
    st.subheader(f"Quick Select {asset_type}")
    for symbol, name in watchlist.items():
        if st.button(f"{symbol} - {name}", key=f"btn_{symbol}", use_container_width=True):
            ticker_input = symbol 
            
    st.write("---")
    run_btn = st.button("🚀 Run Deep Analysis", type="primary", use_container_width=True)

# --- 4. MAIN APP LOGIC ---
if run_btn or ticker_input:
    try:
        info = fetch_finance_data(ticker_input)
        is_etf = info.get('quoteType') == 'ETF'
        curr_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice')

        # Logic for Scoring
        if not is_etf:
            pe, f_pe, ps, pb = info.get('trailingPE'), info.get('forwardPE'), info.get('priceToSalesTrailing12Months'), info.get('priceToBook')
            roe, profit_margin = (info.get('returnOnEquity', 0) or 0) * 100, (info.get('profitMargins', 0) or 0) * 100
            debt, current_ratio = (info.get('debtToEquity', 0) or 0) / 100, info.get('currentRatio')
            target = info.get('targetMeanPrice')
            upside = ((target / curr_price) - 1) * 100 if target else 0

            # Scoring Mapping
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
        else:
            total_score = 85 # Standard ETF Strength Baseline
            verdict, color = "🚀 ETF STRENGTH", "green"

        # Verdict Coloring
        if not is_etf:
            if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
            elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
            elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
            else: verdict, color = "🚩 SELL", "red"

        # Display Verdict
        st.markdown(f"""<div style="background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid white;">
            <h1 style="color:white; margin:0;">Verdict: {verdict}</h1>
            <h2 style="color:white; margin:0;">AI Score: {int(total_score)}/100</h2></div>""", unsafe_allow_html=True)

        st.subheader(f"Live Analysis: {info.get('longName', ticker_input)}")
        
        # --- ETF SPECIAL: ABOUT & PORTFOLIO ---
        if is_etf:
            st.divider()
            st.header("📂 ETF Overview & Composition")
            ecol1, ecol2 = st.columns([2, 1])
            with ecol1:
                st.markdown("#### Strategy Description")
                st.write(info.get('longBusinessSummary', "Description not available."))
            with ecol2:
                st.markdown("#### Asset Allocation")
                allocation = {"Asset": ["Stocks", "Bonds", "Cash", "Other"], 
                              "Weight": [info.get('fundProfile', {}).get('stockPosition', 98.5), 
                                         info.get('fundProfile', {}).get('bondPosition', 0.5), 
                                         info.get('fundProfile', {}).get('cashPosition', 1.0), 0]}
                fig = px.pie(allocation, values='Weight', names='Asset', hole=0.5)
                st.plotly_chart(fig, use_container_width=True)

        # --- TRADINGVIEW CHART ---
        tv_widget = f"""<div class="tradingview-widget-container"><div id="tv_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{"width": "100%", "height": 450, "symbol": "{ticker_input}", "interval": "D", "theme": "light", "style": "1", "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]}});
          </script></div>"""
        components.html(tv_widget, height=470)

        # --- DATA TABLES (STOCK ONLY) ---
        if not is_etf:
            st.write("### 📊 Fundamental Audit")
            col_left, col_right = st.columns(2)
            with col_left:
                st.table(pd.DataFrame({"Metric": ["Trailing P/E", "Forward P/E", "P/S Ratio", "P/B Ratio"], 
                                       "Value": [f"{pe:.2f}" if pe else "N/A", f"{f_pe:.2f}" if f_pe else "N/A", f"{ps:.2f}" if ps else "N/A", f"{pb:.2f}" if pb else "N/A"],
                                       "Rating": [l_pe, l_fpe, l_ps, l_pb]}))
            with col_right:
                st.table(pd.DataFrame({"Metric": ["ROE %", "Profit Margin", "Debt/Equity", "Current Ratio"],
                                       "Value": [f"{roe:.2f}%", f"{profit_margin:.2f}%", f"{debt:.2f}", f"{current_ratio:.2f}"],
                                       "Rating": [l_roe, l_margin, l_debt, l_cr]}))

        # --- 7. EXPLANATION SECTION for STOCKS---
        st.divider()
        st.header("📖 Methodology & Indicator Guide")
        t1, t2, t3, t4= st.tabs(["💵 Valuation", "🏆 Performance", "🛡️ Safety","🤖 The Scoring Engine"])

        with t1:
            st.markdown("""
            **P/E (Price to Earnings):** The gold standard for valuation. A P/E under 20 is often considered 'value' territory, while over 40 suggests high growth expectations or a bubble.
            
            **P/S (Price to Sales):** Critical for Tech/SaaS. Shows how much you pay for every $1 of revenue.
            
            **P/B (Price to Book):** Measures the market price against the company's net asset value.
            """)

        with t2:
            st.markdown("""
            **ROE (Return on Equity):** Tells you how much profit the company generates with the money shareholders have invested. Over 18% is elite.
            
            **Profit Margin:** Percentage of revenue left after all expenses. High margins indicate a strong "moat" or brand power.
            """)

        with t3:
            st.markdown("""
            **Debt/Equity:** A ratio of 1.0 means debt equals equity. A ratio < 0.8 means the company owns much more than it owes. 
            High debt (>1.6) is a red flag.
            
            **Current Ratio:** Measures if the company can pay its short-term bills. A ratio > 1.5 is healthy.
            
            **Upside:** The gap between current price and professional analyst targets.
            """)
        with t4:
            st.markdown("""
            ### How the Verdict is Calculated
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
        st.error(f"Analysis failed: {e}")
