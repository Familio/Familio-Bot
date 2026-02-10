import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & CACHING ---
st.set_page_config(layout="wide", page_title="Cicim Unified Bot", page_icon="🏦")

@st.cache_data(ttl=3600)
def fetch_finance_data(ticker):
    """Universal fetcher for both Stocks and ETFs."""
    stock = yf.Ticker(ticker)
    return stock.info

# --- 2. HELPER FUNCTIONS ---
def get_stock_rating(val, metric_type):
    if val in [None, 0, "N/A"]: return "⚪ Neutral", 0
    if metric_type in ["PE", "FPE"]:
        if val < 20: return "✅ Good Value", 20
        if val < 40: return "⚖️ Average", 10
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
    return "⚪ Neutral", 0

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🏦 Cicim Unified")
    mode = st.radio("Select Analysis Mode", ["📈 Stocks", "🧺 ETFs"], help="Switch between Individual Companies and Funds.")
    st.divider()
    
    ticker_input = st.text_input(f"Enter {mode[:-1]} Symbol", "TSM" if "Stocks" in mode else "VOO").upper()
    run_btn = st.button(f"Analyze {mode[:-1]}", type="primary", use_container_width=True)
    
    if "Stocks" in mode:
        st.write("### Quick Watchlist")
        for sym in ["NVDA", "AAPL", "MSFT", "GOOGL"]:
            if st.button(sym, use_container_width=True): ticker_input = sym

# --- 4. MAIN APP LOGIC ---
if ticker_input:
    try:
        info = fetch_finance_data(ticker_input)
        
        # --- A. STOCK ANALYSIS VIEW ---
        if "Stocks" in mode:
            st.title(f"Analysis: {info.get('longName', ticker_input)}")
            
            # Data Extraction
            pe = info.get('trailingPE')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            target = info.get('targetMeanPrice')
            curr_price = info.get('currentPrice', 1)
            upside = ((target / curr_price) - 1) * 100 if target else 0

            # Scoring
            _, s_pe = get_stock_rating(pe, "PE")
            _, s_roe = get_stock_rating(roe, "ROE")
            _, s_debt = get_stock_rating(debt, "DEBT")
            
            fundamental_score = (s_pe + s_roe + s_debt) * 1.66 # Scale to ~100
            tech_score = 30 if upside > 15 else (15 if upside > 0 else 0)
            total_score = (fundamental_score * 0.7) + tech_score

            # UI Display
            st.metric("Total Stock Score", f"{int(total_score)} / 100")
            col1, col2, col3 = st.columns(3)
            col1.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
            col2.metric("ROE", f"{roe:.1f}%")
            col3.metric("Upside", f"{upside:.1f}%")

        # --- B. ETF ANALYSIS VIEW ---
        else:
            st.title(f"Fund Analysis: {info.get('longName', ticker_input)}")
            
            # Data Extraction
            exp_ratio = info.get('annualReportExpenseRatio', 0.001) or 0
            yield_pct = (info.get('trailingAnnualDividendYield', 0) or 0) * 100
            aum = info.get('totalAssets', 0) or 0
            
            # Scoring
            etf_score = 0
            if exp_ratio <= 0.10: etf_score += 50
            elif exp_ratio <= 0.30: etf_score += 30
            if aum > 1_000_000_000: etf_score += 30
            if yield_pct > 2: etf_score += 20

            # UI Display
            st.metric("Efficiency Score", f"{etf_score} / 100")
            col1, col2, col3 = st.columns(3)
            col1.metric("Expense Ratio", f"{exp_ratio:.2%}", delta="Cheap" if exp_ratio < 0.1 else "Pricey", delta_color="inverse")
            col2.metric("Div. Yield", f"{yield_pct:.2f}%")
            col3.metric("AUM", f"${aum/1e9:.1f}B")

        # --- C. SHARED INTERACTIVE CHART ---
        st.divider()
        st.subheader("Interactive Market Chart")
        tradingview_widget = f"""
        <div class="tradingview-widget-container"><div id="tv_chart"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">new TradingView.widget({{"width": "100%", "height": 450, "symbol": "{ticker_input}", "interval": "D", "theme": "light"}});</script></div>
        """
        components.html(tradingview_widget, height=470)

    except Exception as e:
        st.error(f"Could not analyze {ticker_input}. Error: {e}")

# --- 5. UNIFIED EXPLANATION ---
with st.expander("📖 How the Scores Work"):
    st.markdown("""
    * **Stocks:** Uses the '5 Pillars' (PE, ROE, Debt, etc.) to judge if the business is healthy.
    * **ETFs:** Uses 'Efficiency Metrics' (Fees, Assets, Yield) to judge if the fund is a good bucket for your money.
    """)
