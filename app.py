# --- 2. IMPROVED RATING LOGIC ---
def get_rating(val, metric_type, sector="Other"):
    """Calculates status and points with Sector-Awareness"""
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 20
        if val < 40: return "⚖️ Average", 10
        return "⚠️ Pricey", 0
        
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 20
        if val > 8: return "⚖️ Average", 10
        return "🐌 Slow", 0

    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 20
        if val < 1.6: return "⚖️ Average", 10
        return "🚩 Risky Debt", 0

    if metric_type == "PS":
        if val < 2.0: return "✅ Fair Sales", 20
        if val < 5.0: return "⚖️ Moderate", 10
        return "⚠️ High Premium", 0

    if metric_type == "PB":
        # TECH ADJUSTMENT: Tech companies naturally have higher P/B
        if sector in ["Technology", "Communication Services"]:
            if val < 8.0: return "💎 Tech Value", 20
            if val < 15.0: return "⚖️ Tech Fair", 10
            return "⚠️ Asset Heavy", 0
        else:
            # Traditional Value Standards
            if val < 1.5: return "💎 Undervalued", 20
            if val < 4.0: return "⚖️ Fair Assets", 10
            return "⚠️ Asset Heavy", 0

# --- 3. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Control Panel")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="6mo")

        if hist.empty:
            st.error("Could not find data for this symbol.")
        else:
            # 4a. Sector Detection
            stock_sector = info.get('sector', 'Other')
            
            # 4b. Extract Metrics
            trailing_pe = info.get('trailingPE')
            f_pe = info.get('forwardPE')
            roe = (info.get('returnOnEquity', 0) or 0) * 100
            debt = (info.get('debtToEquity', 0) or 0) / 100
            ps_ratio = info.get('priceToSalesTrailing12Months')
            pb_ratio = info.get('priceToBook')

            # 4c. Run Scoring with Sector Logic
            pe_label, pe_score = get_rating(trailing_pe, "PE")
            roe_label, roe_score = get_rating(roe, "ROE")
            debt_label, debt_score = get_rating(debt, "DEBT")
            ps_label, ps_score = get_rating(ps_ratio, "PS")
            pb_label, pb_score = get_rating(pb_ratio, "PB", sector=stock_sector)
            
            total_score = pe_score + roe_score + debt_score + ps_score + pb_score
            
            # ... (Visualization and Table code same as before)
            st.subheader(f"Analysis for {info.get('longName')} ({stock_sector})")
            
            # --- 6. DATA TABLE ---
            full_data = {
                "Metric": ["P/E (TTM)", "P/S Ratio", "P/B Ratio", "ROE %", "Debt/Equity", "TOTAL SCORE"],
                "Value": [f"{trailing_pe:.2f}" if trailing_pe else "N/A", 
                          f"{ps_ratio:.2f}" if ps_ratio else "N/A",
                          f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                          f"{roe:.2f}%", f"{debt:.2f}", f"{total_score}/100"],
                "Status": [pe_label, ps_label, pb_label, roe_label, debt_label, "Rating: " + str(total_score)]
            }
            st.table(pd.DataFrame(full_data))

# --- 7. DETAILED METHODOLOGY EXPANDER ---
            st.divider()
            with st.expander("🚦 Deep Dive: Scoring Methodology & Indicators"):
                st.markdown(f"""
                ### 🏆 How the {total_score}/100 Score is Calculated
                The bot uses a **Weighted Simple Additive Scoring** method. Each of the 5 indicators is a "health check" worth exactly **20 points**.
                
                **Calculation Formula:**
                $Total Score = S_{{PE}} + S_{{PS}} + S_{{PB}} + S_{{ROE}} + S_{{DEBT}}$
                
                | Indicator | ✅ 20 Points (Best) | ⚖️ 10 Points (Fair) | ⚠️ 0 Points (Poor) |
                | :--- | :--- | :--- | :--- |
                | **P/E Ratio** | < 20 | 20 - 40 | > 40 |
                | **P/S Ratio** | < 2.0 | 2.0 - 5.0 | > 5.0 |
                | **P/B Ratio** | < 1.5 | 1.5 - 4.0 | > 4.0 |
                | **ROE %** | > 18% | 8% - 18% | < 8% |
                | **Debt/Equity**| < 0.8 | 0.8 - 1.6 | > 1.6 |

                ---

                ### 🔍 Indicator Logic in the Code
                1. **P/E (Price-to-Earnings):** We use **TTM (Trailing Twelve Months)** as the primary scoring metric because it is based on audited past performance. **Forward P/E** is shown for context on analyst expectations.
                2. **P/S (Price-to-Sales):** This measures how much you pay for every $1 of sales. It is crucial for high-growth tech companies that might not have high profits yet.
                3. **P/B (Price-to-Book):** This tells you the "floor" value of the stock based on the company's balance sheet.
                4. **ROE (Return on Equity):** This is calculated as: $\\text{{ROE}} = \\frac{{\\text{{Net Income}}}}{{\\text{{Shareholder Equity}}}}$. It shows how efficiently management uses your money.
                5. **Debt-to-Equity:** This measures the company's leverage. A score of 0.5 means for every $1 of equity, the company has $0.50 in debt.

                **Rating Tiers:**
                * **80-100:** 💎 **Strong Buy Candidate** - Excellent value and safety.
                * **50-70:** ⚖️ **Hold / Average** - Good, but potentially overvalued or high debt.
                * **Below 50:** 🚩 **High Risk** - Poor fundamentals or extreme "hype" pricing.
                """)
    except Exception as e:
        st.error(f"Error processing {ticker_input}: {e}")
