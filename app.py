import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Advanced Indian Market Tracker", layout="wide")
st.title("📈 Advanced Indian Market Sector Dashboard")

# 1. Setup default lists in background memory (Session State)
if "sectors_data" not in st.session_state:
    st.session_state.sectors_data = {
        "Nifty 50": ["^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Bank Nifty": ["^NSEBANK", "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFCBANK.NS"],
        "Nifty IT Sector": ["^CNXIT", "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
        "Nifty FMCG Sector": ["^CNXFMCG", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS"]
    }

# 2. Sidebar Management Console (Add / Remove Stocks)
st.sidebar.header("🛠️ Manage Sector Stocks")
selected_sector = st.sidebar.selectbox("Select Sector Dashboard", list(st.session_state.sectors_data.keys()))
current_stock_list = st.session_state.sectors_data[selected_sector]

st.sidebar.subheader("➕ Add New Stock")
new_stock = st.sidebar.text_input("Type NSE Ticker (e.g., SBIN.NS)").strip().upper()
if st.sidebar.button("Add to Sector List"):
    if new_stock and new_stock not in current_stock_list:
        st.session_state.sectors_data[selected_sector].append(new_stock)
        st.success(f"Added {new_stock}!")
        st.rerun()

st.sidebar.subheader("❌ Remove a Stock")
if len(current_stock_list) > 1:
    remove_stock = st.sidebar.selectbox("Choose stock to drop", current_stock_list)
    if st.sidebar.button("Remove from Sector List"):
        st.session_state.sectors_data[selected_sector].remove(remove_stock)
        st.warning(f"Removed {remove_stock}!")
        st.rerun()

# 3. Setup Target Timelines
time_frames = {
    "1 Day": 1, "3 Days": 3, "1 Week": 7, "1 Month": 30,
    "2 Months": 60, "3 Months": 90, "6 Months": 180, "1 Year": 365
}

matrix = []
today = datetime.today()

with st.spinner("Calculating moving averages and matrix arrays..."):
    for ticker in current_stock_list:
        try:
            # Fetch a wider range (700 days) to accurately measure 1-year returns and 52-week parameters
            df = yf.download(ticker, start=(today - timedelta(days=700)).strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
            
            if not df.empty:
                # 🔥 Bulletproof Fix: Standardize multi-layered headers immediately
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Strip down to only columns containing raw lists
                df = df.loc[:, ~df.columns.duplicated()]
                
                # Extract pricing arrays safely
                close_series = df['Close'].dropna()
                high_series = df['High'].dropna()
                low_series = df['Low'].dropna()
                
                current_close = float(close_series.iloc[-1])
                
                # Calculate Technical Moving Averages
                ma4 = round(float(close_series.rolling(window=4).mean().iloc[-1]), 2) if len(close_series) >= 4 else None
                ma20 = round(float(close_series.rolling(window=20).mean().iloc[-1]), 2) if len(close_series) >= 20 else None
                ma50 = round(float(close_series.rolling(window=50).mean().iloc[-1]), 2) if len(close_series) >= 50 else None
                
                # Fetch 52-Week Extremes (Approx 252 active market trading sessions)
                past_year_data_high = high_series.iloc[-252:] if len(high_series) >= 252 else high_series
                past_year_data_low = low_series.iloc[-252:] if len(low_series) >= 252 else low_series
                
                high_52w = round(float(past_year_data_high.max()), 2)
                low_52w = round(float(past_year_data_low.min()), 2)
                
                # Compile base metrics row
                row = {
                    "Stock/Index": ticker,
                    "Current Price": round(current_close, 2),
                    "4 MA": ma4,
                    "20 MA": ma20,
                    "50 MA": ma50,
                    "52W High": high_52w,
                    "52W Low": low_52w
                }
                
                # Compute returns across custom timelines
                for label, days in time_frames.items():
                    target_date = close_series.index[-1] - timedelta(days=days)
                    idx = close_series.index.get_indexer([target_date], method='pad')[0]
                    past_price = float(close_series.iloc[idx])
                    row[label] = round(((current_close - past_price) / past_price) * 100, 2)
                
                matrix.append(row)
        except Exception:
            continue

# 4. Display Clean Visual Data Frames
st.subheader(f"📊 Live Technical View: {selected_sector}")
if matrix:
    df_final = pd.DataFrame(matrix)
    
    # Reordering columns to place prices and technical MAs first, followed by returns
    column_order = ["Stock/Index", "Current Price", "4 MA", "20 MA", "50 MA", "52W High", "52W Low", 
                    "1 Day", "3 Days", "1 Week", "1 Month", "2 Months", "3 Months", "6 Months", "1 Year"]
    df_final = df_final[[col for col in column_order if col in df_final.columns]]
    
    st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("No data compiled. Add valid NSE symbols to populate your workspace layout.")
