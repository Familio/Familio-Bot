import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG & AUTH ---
st.set_page_config(layout="wide", page_title="Cicim ETF Bot", page_icon="🧺")

def check_password():
    def password_entered():
        if st.session_state["password"] == "etf2026": # CHANGE THIS PASSWORD
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("🔑 Enter Bot Password", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state["password_correct"]

if check_password():
    st.title("🧺 Cicim ETF Bot: Efficiency & Yield Analyzer")

    # --- 2. CACHED DATA FETCHING ---
    @st.cache_data(ttl=3600)
    def get_etf_data(ticker_symbol):
        etf = yf.Ticker(ticker_symbol)
        return etf.info

    # --- 3. SIDEBAR ---
    with st.sidebar:
        st.header("ETF Search")
        ticker = st.text_input("Enter ETF Ticker (e.g., VOO, SCHD, JEPI)", "SCHD").upper()
        analyze_btn = st.button("🔍 Analyze Fund", type="primary", use_container_width=True)
        st.divider()
        st.info("💡 Best 2026 Picks:\n- VOO (Growth)\n- SCHD (Dividends)\n- JEPI (Income)")

    # --- 4. MAIN LOGIC ---
    if analyze_btn or ticker:
        try:
            info = get_etf_data(ticker)
            
            # Extract ETF Specifics
            name = info.get('longName', 'Unknown ETF')
            exp_ratio = info.get('annualReportExpenseRatio', 0) 
            if exp_ratio is None: exp_ratio = 0
            
            yield_pct = (info.get('trailingAnnualDividendYield', 0) or 0) * 100
            aum = info.get('totalAssets', 0) or 0
            price = info.get('currentPrice', info.get('navPrice', 0))

            # --- 5. ETF SCORING ENGINE ---
            score = 0
            # 5a. Expense Ratio Score (Lower is better)
            if exp_ratio <= 0.08: score += 40
            elif exp_ratio <= 0.20: score += 25
            elif exp_ratio <= 0.50: score += 10
            
            # 5b. Yield & Size Score
            if yield_pct > 3: score += 30
            elif yield_pct > 1: score += 20
            if aum > 1_000_000_000: score += 10 # Bonus for liquidity

            # 5c. Verdict Mapping
            if score >= 70: verdict, color = "💎 CORE HOLDING", "green"
            elif score >= 40: verdict, color = "⚖️ SPECULATIVE", "orange"
            else: verdict, color = "🚩 AVOID / EXPENSIVE", "red"

            # --- 6. DISPLAY RESULTS ---
            st.markdown(f"""
                <div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;">
                    <h1 style="color:white; margin:0;">{verdict}</h1>
                    <h2 style="color:white; margin:0;">Efficiency Score: {score}/100</h2>
                </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Expense Ratio", f"{exp_ratio:.2%}", delta="LOW FEE" if exp_ratio < 0.1 else "HIGH FEE", delta_color="inverse")
            col2.metric("Dividend Yield", f"{yield_pct:.2f}%")
            col3.metric("Assets (AUM)", f"${aum/1e9:.1f}B")

            # Chart
            st.write(f"### {ticker} Performance Chart")
            tradingview_widget = f"""
            <div class="tradingview-widget-container"><div id="tv_chart"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">new TradingView.widget({{"width": "100%", "height": 400, "symbol": "{ticker}", "interval": "D", "theme": "light"}});</script></div>
            """
            components.html(tradingview_widget, height=420)

            # --- 7. EXPLANATION SECTION ---
            with st.expander("📖 Why these indicators matter for ETFs"):
                st.markdown("""
                ### 💸 The Expense Ratio (Your Silent Killer)
                An ETF with a **0.50%** fee might not seem bad, but over 30 years, it can eat **15-20% of your total wealth**. We prioritize funds under **0.10%** for maximum ROI.

                ### 🏛️ AUM (Assets Under Management)
                If an ETF has less than **$100M** in assets, it is at risk of closing down. Larger funds (like VOO) are safer and easier to trade.

                ### 📈 Yield (Income Generation)
                * **Growth ETFs (VOO/QQQ):** Low yield (~1%), high price appreciation.
                * **Income ETFs (SCHD/JEPI):** High yield (3-10%), slower price growth.
                """)

        except Exception as e:
            st.error(f"Error: {e}. Some ETFs do not provide all data points via public APIs.")
