import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Cicim Bot Pro")
st.title("🤖 Cicim Bot: Professional Stock Analysis")

# --- 2. RATING LOGIC ---
def get_rating(val, metric_type):
    """Calculates status and points for the overall score"""
    if val == "N/A" or val is None or val == 0: 
        return "⚪ Neutral", 0
    
    if metric_type == "PE":
        if val < 20: return "✅ Good Value", 33
        if val < 40: return "⚖️ Average", 15
        return "⚠️ Pricey", 0
        
    if metric_type == "ROE":
        if val > 18: return "🔥 High Power", 34
        if val > 8: return "⚖️ Average", 15
        return "🐌 Slow", 0

    if metric_type == "DEBT":
        if val < 0.8: return "🛡️ Very Safe", 33
        if val < 1.6: return "⚖️ Average", 15
        return "🚩 Risky Debt", 0

# --- 3. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("Control Panel")
    api_key = st.text_input("Gemini API Key", type="password")
    ticker_input = st.text_input("Stock Symbol", "TSM").upper()
    run_btn = st.button("🚀 Run Analysis")

# --- 4. MAIN APP LOGIC ---
if run_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key!")
    else:
        try:
            # Fetch Data
            stock = yf.Ticker(ticker_input)
            info = stock.info
            hist = stock.history(period="6mo")

            if hist.empty:
                st.error("Could not find data for this symbol. Please check the ticker.")
            else:
                # 4a. Extract Data
                mkt_cap = info.get('marketCap', 0)
                trailing_pe = info.get('trailingPE')
                f_pe = info.get('forwardPE')
                roe = info.get('returnOnEquity', 0) * 100
                debt = info.get('debtToEquity', 0) / 100
                cap_str = f"${mkt_cap/1e12:.2f}T" if mkt_cap >= 1e12 else f"${mkt_cap/1e9:.2f}B"

                # 4b. Calculate Individual & Total Scores
                pe_label, pe_score = get_rating(f_pe if f_pe else trailing_pe, "PE")
                roe_label, roe_score = get_rating(roe, "ROE")
                debt_label, debt_score = get_rating(debt, "DEBT")
                total_score = pe_score + roe_score + debt_score
                
                # Determine Status
                if total_score >= 80: total_status = "💎 Strong Buy Candidate"
                elif total_score >= 40: total_status = "⚖️ Average / Hold"
                else: total_status = "🚩 High Risk / Avoid"

                # --- 5. VISUALS: CANDLE CHART ---
                st.subheader(f"Price Action: {ticker_input}")
                fig = go.Figure(data=[go.Candlestick(
                    x=hist.index,
                    open=hist['Open'], high=hist['High'],
                    low=hist['Low'], close=hist['Close'],
                    increasing_line_color='green', decreasing_line_color='red'
                )])
                fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=500)
                st.plotly_chart(fig, use_container_width=True)

                # --- 6. THE DATA TABLE (Fixed with string conversion) ---
                st.divider()
                st.subheader("Fundamental Scorecard")
                
                full_data = {
                    "Metric": ["Price", "Market Cap", "P/E (TTM)", "Forward P/E", "ROE", "Debt/Equity", "OVERALL SCORE"],
                    "Value": [
                        f"${info.get('currentPrice', 'N/A')}", 
                        cap_str, 
                        f"{trailing_pe:.2f}" if trailing_pe else "N/A", 
                        f"{f_pe:.2f}" if f_pe else "N/A", 
                        f"{roe:.2f}%", 
                        f"{debt:.2f}", 
                        f"{total_score}/100"
                    ],
                    "Status": ["Current", "Market Size", "Historical", pe_label, roe_label, debt_label, total_status]
                }
                
                # Convert to string to prevent Arrow serialization errors
                df_display = pd.DataFrame(full_data).astype(str)
                st.table(df_display)

        except Exception as e:
            st.error(f"Error processing {ticker_input}: {e}")
