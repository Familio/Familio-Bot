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
            insider_own = (info.get('heldPercentInsiders', 0) or 0) * 100
            insider_trans = (info.get('insiderTransactionsRatio', 0) or 0) * 100
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
                    <p style="color:gray; font-size: 12px;">Based on {analyst_count} analysts</p></div>""", unsafe_allow_html=True)

        st.subheader(f"Live Analysis: {info.get('longName', ticker_input)}")
        
        if is_etf:
            st.divider()
            st.header("📂 ETF Overview & Composition")
            ecol1, ecol2 = st.columns([2, 1])
            with ecol1:
                st.write(info.get('longBusinessSummary', "Description not available."))
            with ecol2:
                allocation = {"Asset": ["Stocks", "Bonds", "Cash", "Other"], 
                              "Weight": [info.get('fundProfile', {}).get('stockPosition', 98.5), 
                                         info.get('fundProfile', {}).get('bondPosition', 0.5), 
                                         info.get('fundProfile', {}).get('cashPosition', 1.0), 0]}
                st.plotly_chart(px.pie(allocation, values='Weight', names='Asset', hole=0.5), use_container_width=True)

        # Chart
        tv_widget = f"""<div class="tradingview-widget-container"><div id="tv_chart"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{"width": "100%", "height": 450, "symbol": "{ticker_input}", "interval": "D", "theme": "light", "style": "1", "studies": ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"]}});
          </script></div>"""
        components.html(tv_widget, height=470)

        # Audit Tables
        if not is_etf:
            st.write("### 📊 Fundamental Audit")
            col_left, col_right = st.columns(2)
            insider_signal = "🟢 Buying" if insider_trans > 0 else ("🔴 Selling" if insider_trans < 0 else "⚪ Static")
            
            with col_left:
                st.table(pd.DataFrame({"Metric": ["Trailing P/E", "PEG Ratio", "P/S Ratio", "Insider Own %", "Insider Trans (6M)"], 
                                       "Value": [f"{pe:.2f}" if pe else "N/A", f"{peg:.2f}" if peg else "N/A", f"{ps:.2f}" if ps else "N/A", f"{insider_own:.2f}%", f"{insider_trans:.2f}%"],
                                       "Rating": [l_pe, l_peg, l_ps, "🔍 Sentiment", insider_signal]}))
            with col_right:
                st.table(pd.DataFrame({"Metric": ["ROE %", "ROIC %", "Profit Margin", "Debt/Equity", "Short Interest %"],
                                       "Value": [f"{roe:.2f}%" if roe else "N/A", f"{roic:.2f}%" if roic else "N/A", f"{profit_margin:.2f}%" if profit_margin else "N/A", f"{debt:.2f}" if debt else "N/A", f"{short_ratio:.2f}%"],
                                       "Rating": [l_roe, l_roic, l_margin, l_debt, "⚠️ Risk Factor"]}))

        # --- 7. DETAILED METHODOLOGY GUIDE ---
        st.divider()
        st.header("📖 Methodology & Indicator Guide")
        t1, t2, t3, t4 = st.tabs(["💵 Valuation", "🏆 Efficiency", "🛡️ Safety & Insiders", "🤖 AI Engine"])

        with t1:
            st.markdown("""
            ### Understanding Valuation
            * **Trailing P/E Ratio**: Compares the current share price to the last 12 months of earnings. A low P/E suggests the stock is "cheap" relative to its profit.
            * **PEG Ratio (Price/Earnings to Growth)**: The most critical metric for growth stocks. It adjusts the P/E by the company's growth rate. A **PEG < 1.0** indicates you are getting growth at a discount.
            * **P/S Ratio (Price to Sales)**: Measures the market price against total revenue. Vital for valuing high-growth companies that are not yet profitable.
            * **P/B Ratio (Price to Book)**: Compares market value to "book value" (assets minus liabilities). High P/B often indicates a company with a strong brand or intellectual property.
            """)
            
        with t2:
            st.markdown("""
            ### Measuring Management Quality
            * **ROIC (Return on Invested Capital)**: The **Gold Standard** of efficiency. It measures how much profit a company generates for every $1 of total capital (debt + equity) invested. Values **>15%** indicate a strong competitive moat.
            * **ROE (Return on Equity)**: Measures profitability from the shareholder's perspective. High ROE indicates management is efficient at using investors' money to grow the business.
            * **Profit Margin**: The percentage of revenue left after all expenses. High margins (>20%) signal pricing power and a superior product.
            """)
            
        with t3:
            st.markdown("""
            ### Safety, Risk, and Insider Sentiment
            * **Insider Ownership**: The percentage of shares owned by executives and directors. High ownership aligns the CEO's interests with yours.
            * **Insider Transactions (6M)**: Shows if insiders have been net buyers or sellers over the last 6 months.
                * **🟢 Net Buying**: Strong signal of internal confidence. Insiders buy for only one reason: they expect the price to rise.
                * **🔴 Net Selling**: Can be profit-taking or tax-related, but massive selling is a warning.
            * **Short Interest %**: The percentage of shares being bet against. High short interest (>10%) can signal market skepticism or a potential "short squeeze."
            * **Debt to Equity**: Measures financial leverage. A ratio **<0.8** is conservative and safe.
            """)

        with t4:
            st.markdown(r"""
            ### The Weighted Algorithm
            The bot uses a multivariate weighting system to generate the 0-100 score:
            
            1.  **Fundamental Base (70%)**: Aggregates 9 key metrics across Valuation, Efficiency, and Debt.
            2.  **Wall Street Sentiment (30%)**: Calculates the percentage "Gap" between current price and the Analyst Mean Target.
            
            $$Total\ Score = \left(\frac{\sum Metrics}{1.8} \times 0.7\right) + Upside\ Bonus$$
            
            **Thresholds:**
            * **80+ (Strong Buy)**: Rare elite companies at attractive prices.
            * **60-79 (Buy)**: Solid businesses with moderate upside.
            * **40-59 (Hold)**: Fairly valued; risk and reward are balanced.
            * **<40 (Sell)**: High debt, poor efficiency, or extreme overvaluation.
            """)

    except Exception as e:
        st.error(f"Analysis failed: {e}")
