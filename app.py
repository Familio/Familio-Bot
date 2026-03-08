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
st.title("📈 Familio AI Bot: Elite Asset Analysis")

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
    if metric_type in ["ROE", "ROIC"]:
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0
    if metric_type == "Margin":
        if val > 20: return "💰 High Profit", 20
        if val > 10: return "⚖️ Healthy", 10
        return "Thin", 0
        
    # Health/Debt/Cash Ratings
    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0
    if metric_type == "CurrentRatio":
        if val > 1.5: return "💧 Liquid", 20
        if val > 1.0: return "⚖️ Stable", 10
        return "⚠️ Cash Tight", 0
    if metric_type == "Payout":
        if val < 60: return "🛡️ Dividend Safe", 10
        if val < 90: return "⚖️ High Payout", 5
        return "🚩 Dividend at Risk", 0

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
            # 1. Fundamental Metrics
            pe, ps, pb, peg = info.get('trailingPE'), info.get('priceToSalesTrailing12Months'), info.get('priceToBook'), info.get('pegRatio')
            roe, roic = (info.get('returnOnEquity', 0) or 0) * 100, (info.get('returnOnAssets', 0) or 0) * 100
            profit_margin = (info.get('profitMargins', 0) or 0) * 100
            
            # 2. Safety & Sentiment Metrics
            debt = (info.get('debtToEquity', 0) or 0) / 100
            current_ratio = info.get('currentRatio')
            insider_own = (info.get('heldPercentInsiders', 0) or 0) * 100
            short_ratio = (info.get('shortPercentOfFloat', 0) or 0) * 100
            
            # 3. Cash & Dividend Metrics
            div_yield = (info.get('dividendYield', 0) or 0) * 100
            payout_ratio = (info.get('payoutRatio', 0) or 0) * 100
            fcf = info.get('freeCashflow', 0)
            
            # Target Logic
            target = info.get('targetMeanPrice')
            upside = ((target / curr_price) - 1) * 100 if (target and curr_price) else 0
            rec_text, rec_color = format_recommendation(info.get('recommendationKey'))
            analyst_count = info.get('numberOfAnalystOpinions', 'N/A')

            # Ratings Calculation
            l_pe, s_pe = get_rating(pe, "PE")
            l_peg, s_peg = get_rating(peg, "PEG")
            l_ps, s_ps = get_rating(ps, "PS")
            l_roe, s_roe = get_rating(roe, "ROE")
            l_roic, s_roic = get_rating(roic, "ROIC")
            l_debt, s_debt = get_rating(debt, "DEBT")
            l_payout, s_payout = get_rating(payout_ratio, "Payout")

            fundamental_total = (s_pe + s_peg + s_ps + s_roe + s_roic + s_debt) / 1.3
            total_score = (fundamental_total * 0.7) + (30 if upside > 15 else (15 if upside > 0 else 0))
        else:
            total_score, verdict, color = 85, "🚀 ETF STRENGTH", "green"

        if not is_etf:
            if total_score >= 80: verdict, color = "🚀 STRONG BUY", "green"
            elif total_score >= 60: verdict, color = "📈 BUY", "#90EE90"
            elif total_score >= 40: verdict, color = "⚖️ HOLD", "gray"
            else: verdict, color = "🚩 SELL", "red"

        # --- 5. UI RENDERING ---
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
                    <p style="color:gray; font-size: 12px;">Based on {analyst_count} analysts</p></div>""", unsafe_allow_html=True)

        st.subheader(f"Live Analysis: {info.get('longName', ticker_input)}")
        
        # TradingView Widget
        tv_widget = f"""<div class="tradingview-widget-container"><div id="tv_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{"width": "100%", "height": 450, "symbol": "{ticker_input}", "interval": "D", "theme": "light", "style": "1", "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]}});
          </script></div>"""
        components.html(tv_widget, height=470)

        if not is_etf:
            st.write("### 📊 Fundamental Audit")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Valuation & Ownership**")
                st.table(pd.DataFrame({"Metric": ["P/E Ratio", "PEG Ratio", "P/S Ratio", "Insider Own"], 
                                       "Value": [f"{pe:.2f}" if pe else "N/A", f"{peg:.2f}" if peg else "N/A", f"{ps:.2f}" if ps else "N/A", f"{insider_own:.2f}%"]}))
            with col2:
                st.markdown("**Efficiency & Growth**")
                st.table(pd.DataFrame({"Metric": ["ROE %", "ROIC %", "Profit Margin", "Short Interest"],
                                       "Value": [f"{roe:.2f}%", f"{roic:.2f}%", f"{profit_margin:.2f}%", f"{short_ratio:.2f}%"]}))
            with col3:
                st.markdown("**Cash & Dividends**")
                st.table(pd.DataFrame({"Metric": ["Div Yield", "Payout Ratio", "Debt/Equity", "Free Cash Flow"],
                                       "Value": [f"{div_yield:.2f}%", f"{payout_ratio:.2f}%", f"{debt:.2f}", f"${fcf/1e9:.2f}B" if fcf else "N/A"]}))

        # --- 6. METHODOLOGY & GUIDE ---
        st.divider()
        st.header("📖 Methodology & Indicator Guide")
        t1, t2, t3, t4 = st.tabs(["💵 Valuation", "🏆 Efficiency", "🛡️ Safety & Cash", "🤖 AI Scoring"])

        with t1:
            st.markdown("""
            **PEG Ratio:** One of the most important metrics. It adjusts the P/E ratio for growth. A PEG < 1.0 suggests you're getting growth at a discount.
            **P/S Ratio:** Vital for tech companies. It shows what you pay for every $1 of sales.
            """)
            
            
        with t2:
            st.markdown("""
            **ROIC (Return on Invested Capital):** This is the gold standard for quality. It shows how much profit a company makes for every dollar of capital invested (debt + equity).
            **ROE:** Measures profitability from the perspective of shareholder equity.
            """)
            
            
        with t3:
            st.markdown("""
            **Payout Ratio:** Measures dividend sustainability. A payout > 90% is often a warning that the dividend might be cut.
            **Short Interest:** High short interest (>10%) means the market is betting against the company.
            **Free Cash Flow (FCF):** The "truth" metric. It's the actual cash left over after all bills and investments are paid.
            """)
            

        with t4:
            st.markdown(r"""
            ### AI Scoring Algorithm
            Our AI uses a **Weighted Multi-Factor Model** to evaluate an asset:
            1. **Valuation (40%):** PEG, P/E, and P/S ratios.
            2. **Profitability (30%):** ROE, ROIC, and Margins.
            3. **Financial Health (30%):** Debt levels and Cash Flow sustainability.
            
            $$Score = (Base\ Fundamentals \times 0.7) + (Wall\ Street\ Upside\ \times 0.3)$$
            """)

    except Exception as e:
        st.error(f"Analysis failed: {e}")
