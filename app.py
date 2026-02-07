import streamlit as st
import yfinance as yf
import pandas as pd
from google import genai

st.set_page_config(layout="wide")
st.title("🤖 Cicim Bot for Stock Analysis")

# SIDEBAR
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("Analyze Now")

def get_rating(val, metric_type):
    """Returns a rating and color based on industry benchmarks"""
    if val == "N/A" or val is None: return "⚪ Neutral", "gray"
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", "green"
        if val < 35: return "⚖️ Average", "orange"
        return "⚠️ Pricey", "red"
        
    if metric_type == "ROE":
        if val > 20: return "🔥 High Power", "green"
        if val > 10: return "⚖️ Average", "orange"
        return "🐌 Slow", "red"

    if metric_type == "DEBT":
        if val < 0.5: return "🛡️ Very Safe", "green"
        if val < 1.5: return "⚖️ Average", "orange"
        return "🚩 Risky Debt", "red"

if run_btn:
    if not api_key:
        st.error("Please enter your API Key!")
    else:
        try:
            stock = yf.Ticker(ticker_input)
            info = stock.info
            
            # --- DATA EXTRACTION ---
            market_cap = info.get('marketCap')
            trailing_pe = info.get('trailingPE')
            forward_pe = info.get('forwardPE')
            roe = info.get('returnOnEquity', 0) * 100
            debt = info.get('debtToEquity', 0) / 100 
            
            # --- RATINGS ---
            pe_to_rate = forward_pe if forward_pe else trailing_pe
            pe_label, pe_col = get_rating(pe_to_rate, "PE")
            roe_label, roe_col = get_rating(roe, "ROE")
            debt_label, debt_col = get_rating(debt, "DEBT")

            # --- DISPLAY DASHBOARD ---
            st.subheader(f"Summary for {ticker_input}: {info.get('longName', '')}")
            
            # Metric Row 1: Key Financials
            c1, c2, c3, c4 = st.columns(4)
            # Formatting Market Cap to be readable (Billion/Trillion)
            if market_cap:
                formatted_cap = f"${market_cap/1e12:.2f}T" if market_cap >= 1e12 else f"${market_cap/1e9:.2f}B"
            else:
                formatted_cap = "N/A"
                
            c1.metric("Market Cap", formatted_cap)
            c2.metric("Forward P/E", f"{forward_pe:.2f}" if forward_pe else "N/A", pe_label)
            c3.metric("ROE %", f"{roe:.2f}%", roe_label)
            c4.metric("Debt/Equity", f"{debt:.2f}", debt_label)

            # --- DETAILED TABLE ---
            st.divider()
            full_data = {
                "Metric": ["Current Price", "Market Cap", "Trailing P/E", "Forward P/E", "ROE", "Debt/Equity", "Profit Margin"],
                "Value": [
                    f"${info.get('currentPrice')}", 
                    formatted_cap,
                    f"{trailing_pe:.2f}" if trailing_pe else "N/A",
                    f"{forward_pe:.2f}" if forward_pe else "N/A", 
                    f"{roe:.2f}%", 
                    f"{debt:.2f}", 
                    f"{info.get('profitMargins',0)*100:.2f}%"
                ],
                "Status": ["Current", "Size", "Historical Value", pe_label, roe_label, debt_label, "N/A"]
            }
            st.table(pd.DataFrame(full_data))

            # --- AI VERDICT ---
            client = genai.Client(api_key=api_key)
            prompt = (f"Analyze {ticker_input} ({info.get('longName')}). "
                      f"Market Cap: {formatted_cap}, Forward PE: {forward_pe}, ROE: {roe:.2f}%, Debt: {debt}. "
                      f"Give a final rating: BUY, AVERAGE, or AVOID with a 2-sentence justification.")
            
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            st.info("🤖 AI Final Recommendation:")
            st.write(response.text)

        except Exception as e:
            st.error(f"Error: {e}")
