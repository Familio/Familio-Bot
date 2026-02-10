import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components
import plotly.express as px
from datetime import datetime
import pytz

# --- 1. CACHED DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_finance_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.info

@st.cache_data(ttl=3600)
def get_eur_rate():
    """Fetches live USD to EUR exchange rate."""
    try:
        rate = yf.Ticker("USDEUR=X").info.get('regularMarketPrice', 0.92)
        return rate
    except:
        return 0.92 

# --- 2. RATING ENGINE ---
def get_rating(val, metric_type):
    if val in ["N/A", None, 0]: return "⚪ Neutral", 0
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
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0
    if metric_type == "Margin":
        if val > 20: return "💰 High Profit", 20
        if val > 10: return "⚖️ Healthy", 10
        return "Thin", 0
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0
    if metric_type == "CurrentRatio":
        if val > 1.5: return "💧 Liquid", 20
        if val > 1.0: return "⚖️ Stable", 10
        return "⚠️ Cash Tight", 0
    return "⚪ Neutral", 0

# --- 3. SIDEBAR CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Familio AI", page_icon="📈")
st.title("📈 Familio AI Bot: Multi-Asset Terminal")

with st.sidebar:
    st.header("Search & Watchlist")
    
    # Market Status
    tz_cet = pytz.timezone('Europe/Berlin')
    now_cet = datetime.now(tz_cet)
    is_weekend = now_cet.weekday() >= 5
    m_open, m_close = now_cet.replace(hour=15, minute=30, second=0), now_cet.replace(hour=22, minute=0, second=0)
    
    if not is_weekend and m_open <= now_cet <= m_close:
        st.success("🟢 US MARKET OPEN")
    else:
        st.error("🔴 US MARKET CLOSED")
    
    st.write("---")
    asset_type = st.radio("Asset Class", ["Stocks", "ETFs", "Crypto", "Metals"])
    
    # Dynamic Watchlists
    watchlists = {
        "Stocks": {"TSM": "TSMC", "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "COIN": "Coinbase"},
        "ETFs": {"VOO": "S&P 500", "QQQ": "Nasdaq 100", "SCHD": "Dividend", "VGT": "Tech"},
        "Crypto": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "BNB-USD": "Binance"},
        "Metals": {"GC=F": "Gold", "SI=F": "Silver", "PL=F": "Platinum", "HG=F": "Copper"}
    }
    
    ticker_default = list(watchlists[asset_type].keys())[0]
    ticker_input = st.text_input(f"Enter {asset_type} Ticker", ticker_default).upper()
    
    st.subheader(f"Top {asset_type}")
    for symbol, name in watchlists[asset_type].items():
        if st.button(f"{symbol} - {name}", use_container_width=True):
            ticker_input = symbol
            
    run_btn = st.button("🚀 Run Deep Analysis", type="primary", use_container_width=True)

# --- 4. MAIN ANALYSIS LOGIC ---
if run_btn or ticker_input:
    try:
        info = fetch_finance_data(ticker_input)
        q_type = info.get('quoteType', 'UNKNOWN')
        
        # Determine asset category logic
        is_etf = q_type == 'ETF'
        is_crypto = q_type == 'CRYPTOCURRENCY'
        is_commodity = q_type == 'COMMODITY' or ticker_input.endswith('=F')

        # Price Handling
        curr_price_usd = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('navPrice')
        eur_rate = get_eur_rate()
        curr_price_eur = curr_price_usd * eur_rate

        # --- SCORE CALCULATION ---
        if not is_etf and not is_crypto and not is_commodity:
            # Standard Stock Scoring (Existing Logic)
            pe, f_pe, ps, pb = info.get('trailingPE'), info.get('forwardPE'), info.get('priceToSalesTrailing12Months'), info.get('priceToBook')
            roe, margin = (info.get('returnOnEquity', 0) or 0)*100, (info.get('profitMargins', 0) or 0)*100
            debt, cr = (info.get('debtToEquity', 0) or 0)/100, info.get('currentRatio')
            target = info.get('targetMeanPrice')
            upside = ((target / curr_price_usd) - 1) * 100 if target else 0
            
            _, s_pe = get_rating(pe, "PE"); _, s_ps = get_rating(ps, "PS")
            _, s_pb = get_rating(pb, "PB"); _, s_roe = get_rating(roe, "ROE")
            _, s_margin = get_rating(margin, "Margin"); _, s_debt = get_rating(debt, "DEBT")
            _, s_cr = get_rating(cr, "CurrentRatio")
            
            total_score = ((s_pe + s_ps + s_pb + s_roe + s_debt + s_margin + s_cr) / 1.4) * 0.7 + (30 if upside > 15 else 0)
        else:
            # ETFs, Crypto, and Metals get a "Volatility/Trend" based score baseline
            total_score = 75 

        # Verdict Styling
        verdict, color = ("🚀 STRONG BUY", "green") if total_score >= 80 else ("📈 BUY", "#90EE90") if total_score >= 60 else ("⚖️ HOLD", "gray") if total_score >= 40 else ("🚩 SELL", "red")

        # --- HEADER DISPLAY ---
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f'<div style="background-color:{color}; padding:20px; border-radius:15px; text-align:center; border: 2px solid white;"><h1 style="color:white; margin:0;">Verdict: {verdict}</h1><h2 style="color:white; margin:0;">AI Score: {int(total_score)}/100</h2></div>', unsafe_allow_html=True)
        with c2:
            st.metric("Price (USD)", f"${curr_price_usd:,.2f}")
            st.metric("Price (EURO)", f"€{curr_price_eur:,.2f}")

        st.subheader(f"Asset Analysis: {info.get('longName', ticker_input)}")

        # --- SPECIAL SECTIONS ---
        if is_etf or is_crypto or is_commodity:
            st.info(f"Analysis Profile: {q_type.capitalize()}. Multi-factor sentiment analysis applied.")
            st.write(info.get('description', info.get('longBusinessSummary', "No description available.")))

        # --- TRADINGVIEW ---
        tv_symbol = ticker_input.replace("-USD", "") if is_crypto else ticker_input
        components.html(f"""<script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({{"width": "100%", "height": 450, "symbol": "{tv_symbol}", "interval": "D", "theme": "light", "style": "1", "studies": ["RSI@tv-basicstudies"]}});</script>""", height=470)

    except Exception as e:
        st.error(f"Analysis failed: {e}. Check if ticker symbol is correct for Yahoo Finance.")
