import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Indian Market Tracker", layout="wide")
st.title("📈 Custom Indian Sector Tracker")

# 1. Setup default lists in the background memory (Session State)
if "sectors_data" not in st.session_state:
    st.session_state.sectors_data = {
        "Nifty 50": ["^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Bank Nifty": ["^NSEBANK", "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFCBANK.NS"],
        "Nifty IT Sector": ["^CNXIT", "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
        "Nifty FMCG Sector": ["^CNXFMCG", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS"]
    }

# 2. Sidebar Control Panel to Add or Remove Stocks
st.sidebar.header("🛠️ Manage Sector Stocks")

# Choose which sector to look at
selected_sector = st.sidebar.selectbox("Select Sector", list(st.session_state.sectors_data.keys()))
current_stock_list = st.session_state.sectors_data[selected_sector]

# Box to ADD a stock
st.sidebar.subheader("➕ Add New Stock")
new_stock = st.sidebar.text_input("Type NSE Ticker (e.g., BHARTIARTL.NS)").strip().upper()
if st.sidebar.button("Add to Sector"):
    if new_stock and new_stock not in current_stock_list:
        st.session_state.sectors_data[selected_sector].append(new_stock)
        st.success(f"Added {new_stock} successfully!")
        st.rerun()

# Box to REMOVE a stock
st.sidebar.subheader("❌ Remove a Stock")
if len(current_stock_list) > 1:
    remove_stock = st.sidebar.selectbox("Choose stock to remove", current_stock_list)
    if st.sidebar.button("Remove from Sector"):
        st.session_state.sectors_data[selected_sector].remove(remove_stock)
        st.warning(f"Removed {remove_stock}!")
        st.rerun()

# 3. Calculate Returns for the exact timelines you asked for
time_frames = {
    "1 Day": 1, "3 Days": 3, "1 Week": 7, "1 Month": 30,
    "2 Months": 60, "3 Months": 90, "6 Months": 180, "1 Year": 365
}

matrix = []
today = datetime.today()

with st.spinner("Fetching live stock data... Please wait."):
    for ticker in current_stock_list:
        try:
            # Download 1.5 years of history to cover all tracking frames safely
            df = yf.download(ticker, start=(today - timedelta(days=500)).strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
            if not df.empty:
                current_close = float(df['Close'].iloc[-1])
                row = {"Stock/Index": ticker, "Current Price": round(current_close, 2)}
                
                for label, days in time_frames.items():
                    target_date = df.index[-1] - timedelta(days=days)
                    idx = df.index.get_indexer([target_date], method='pad')[0]
                    past_price = float(df['Close'].iloc[idx])
                    
                    # Mathematical change calculation: ((New - Old) / Old) * 100
                    row[label] = round(((current_close - past_price) / past_price) * 100, 2)
                matrix.append(row)
        except Exception:
            continue

# 4. Display the clean data table on screen
st.subheader(f"📊 Showing Returns for: {selected_sector}")
if matrix:
    df_final = pd.DataFrame(matrix)
    st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("No data available. Add stocks using the sidebar.")
