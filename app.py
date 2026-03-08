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
    if metric_type == "PEG":
        if val < 1.0: return "🔥 High Growth Value", 20
        if val < 2.0: return "⚖️ Fair Growth", 10
        return "⚠️ Slow Growth/Overpriced", 0
        
    # Profitability/Efficiency Ratings
    if metric_type == "ROE" or metric_type == "ROIC":
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

def format_recommendation(rec):
    """Formats the yfinance recommendation key."""
    rec_map = {
        "strong_buy": ("🚀 Strong Buy", "#006400"),
        "buy": ("✅ Buy", "#228B22"),
        "hold": ("⚖️ Hold", "#DAA520"),
        "underperform": ("⚠️ Underperform", "#FF4500"),
        "sell": ("🚩 Sell", "#8B0000"),
        "none": ("N/A", "gray")
    }
    return rec_map.get(rec.lower(), ("N/A", "gray")) if rec else ("N/A", "gray")

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

        if not is_etf:
            # Data Extraction
            pe, f_pe, ps, pb = info.get('trailingPE'), info.get('forwardPE'), info.get('priceToSalesTrailing12Months'), info.get('priceToBook')
            peg = info.get('pegRatio')
            roe, roic, profit_margin = (info.get('returnOnEquity', 0) or 0) * 100, (info.get('returnOnAssets', 0) or 0) * 100, (info.get('profitMargins', 0) or 0) * 100
            debt, current_ratio = (info.get('debtToEquity', 0) or 0) / 100, info.get('currentRatio')
            
            # INSIDER DATA
            insider_own = (info.get('heldPercentInsiders', 0) or 0) * 100
            insider_trans = (info.get('insiderTransactionsRatio', 0) or 0) * 100 # Change in insider shares over 6 months
            short_ratio = (info.get('shortPercentOfFloat', 0) or 0) * 100
            
            target = info.get('targetMeanPrice')
            upside = ((target / curr_price) - 1) * 100 if (target and curr_price) else 0
            
            # Analyst Sentiment
            rec_key = info.get('recommendationKey')
            rec_text, rec_color = format_recommendation(rec_key)
            analyst_count = info.get('numberOfAnalystOpinions', 'N/A')

            # Scoring Mapping
            l_pe, s_pe = get_rating(pe, "PE")
            l_fpe, s_fpe = get_rating(f_pe, "FPE") 
            l_ps, s_ps = get_rating(ps, "PS")
            l_pb, s_pb = get_rating(pb, "PB")
            l_peg, s_peg = get_rating(peg, "PEG")
            l_roe, s_roe = get_rating(roe, "ROE")
            l_roic, s_roic = get_rating(roic, "ROIC")
            l_margin, s_margin = get_rating(profit_margin, "Margin")
            l_debt, s_debt = get_rating(debt, "DEBT")
            l_cr, s_cr = get_rating(current_ratio, "CurrentRatio")

            # Weighted Formula
            fundamental_total = (s_pe + s_ps + s_pb + s_roe + s_debt + s_margin + s_cr + s_peg + s_roic) / 1.8
            tech_score = 30 if upside > 15 else (15 if upside > 0 else 0)
            total_score = (fundamental_total * 0.7) + tech_score
        else:
            total_score = 85 
            verdict, color = "🚀 ETF STRENGTH", "green"

        if not is_etf:
            if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
            elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
            elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
            else: verdict, color = "🚩 SELL", "red"

        # Verdict Header
        vcol1, vcol2 = st.columns([2, 1])
        with vcol1:
            st.markdown(f"""<div style="background-color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid white;">
                <h1 style="color:white; margin:0;">Verdict: {verdict}</h1>
                <h2 style="color:white; margin:0;">AI Score: {int(total_score)}/100</h2></div>""", unsafe_allow_html=True)
        with vcol2:
            if not is_etf:
                st.markdown(f"""<div style="background-color:white; padding:25px; border-radius:15px; text-align:center; border: 2px solid {rec_color}; height: 100%;">
                    <h3 style="color:gray; margin:0; font-size: 16px;">Analyst Consensus</h3>
                    <h2 style="color:{rec_color}; margin:10px 0;">{rec_text}</h2>
                    <p style="color:gray; font-size: 12px;">Based on {analyst_count} analysts</p></div>""", unsafe_allow_html
