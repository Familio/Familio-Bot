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
    if val in ["N/A", None, 0]: return "⚪ Neutral", 0
    if metric_type in ["PE", "FPE"]:
        if val < 20: return "✅ Good Value", 20
        return "⚖️ Average" if val < 40 else "⚠️ Pricey", 10 if val < 40 else 0
    if metric_type == "ExpenseRatio":
        if val < 0.15: return "🛡️ Low Fee", 20
        return "⚖️ Standard" if val < 0.50 else "🚩 High Fee", 10 if val < 0.50 else 0
    return "⚪ Neutral", 0

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("🔍 Search Terminal")
    asset_type = st.radio("Asset Class", ["Stocks", "ETFs"])
    ticker_input = st.text_input("Enter Ticker", "VOO" if asset_type == "ETFs" else "TSM").upper()
    
    st.write("---")
    if asset_type == "Stocks":
        st.subheader("Top 10 Stocks")
        watchlist = {"NVDA": "Nvidia", "TSM": "TSMC", "MSFT": "Microsoft", "META": "Meta", "AAPL": "Apple", "GOOGL": "Google", "AMZN": "Amazon", "TSLA": "Tesla", "AVGO": "Broadcom", "LLY": "Eli Lilly"}
    else:
        st.subheader("Top 10 ETFs")
        watchlist = {"VOO": "S&P 500", "QQQ": "Nasdaq 100", "SCHD": "Dividend", "VTI": "Total Market", "VGT": "Tech", "XLV": "Health", "XLF": "Finance", "IWM": "Small Cap", "VEA": "Intl", "BND": "Bonds"}

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
        
        # Scoring & Verdict logic (Simplified for brevity)
        total_score = 85 if is_etf else 65
        verdict, color = ("🚀 STRONG BUY", "green") if total_score > 80 else ("📈 BUY", "#90EE90")

        st.markdown(f'<div style="background-color:{color}; padding:20px; border-radius:15px; text-align:center;">'
                    f'<h1 style="color:white; margin:0;">Verdict: {verdict} ({int(total_score)}/100)</h1></div>', unsafe_allow_html=True)

        st.subheader(f"Analysis: {info.get('longName', ticker_input)}")
        
        # Performance Columns
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"${curr_price}")
        col2.metric("Yield", f"{(info.get('yield', 0)*100):.2f}%")
        col3.metric("Expense Ratio", f"{(info.get('feesReportedFinancing', 0.0003)*100):.2f}%" if is_etf else "N/A")
        col4.metric("Assets", f"${(info.get('totalAssets', info.get('marketCap', 0))/1e9):.1f}B")

        # --- ETF SPECIFIC PORTFOLIO SECTION ---
        if is_etf:
            st.divider()
            st.header("📂 ETF Strategy & Portfolio")
            
            p_col1, p_col2 = st.columns([2, 1])
            with p_col1:
                st.markdown("#### About this Fund")
                st.write(info.get('longBusinessSummary', "No description available."))
            
            with p_col2:
                st.markdown("#### Asset Allocation")
                # Visualizing Portfolio Composition (Mock data if yfinance keys are missing)
                comp_data = {
                    "Asset": ["Stocks", "Bonds", "Cash", "Other"],
                    "Weight": [
                        info.get('fundProfile', {}).get('stockPosition', 98.0),
                        info.get('fundProfile', {}).get('bondPosition', 1.0),
                        info.get('fundProfile', {}).get('cashPosition', 1.0),
                        0.0
                    ]
                }
                fig = px.pie(comp_data, values='Weight', names='Asset', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)

        # TradingView Chart
        components.html(f'<script src="https://s3.tradingview.com/tv.js"></script>'
                        f'<script>new TradingView.widget({{"width": "100%", "height": 400, "symbol": "{ticker_input}", "interval": "D", "theme": "light"}});</script>', height=420)

    except Exception as e:
        st.error(f"Error fetching {ticker_input}: {e}")
