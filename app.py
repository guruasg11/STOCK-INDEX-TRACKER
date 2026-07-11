import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Indian Live Market Tracker", layout="wide")
st.title("📈 Live NSE Market Sector Dashboard")

# 1. Background memory setup (Session State)
if "sectors_data" not in st.session_state:
    st.session_state.sectors_data = {
        "Nifty 50": ["NIFTY", "RELIANCE", "TCS", "HDFCBANK", "INFY"],
        "Bank Nifty": ["BANKNIFTY", "SBIN", "AXISBANK", "ICICIBANK", "HDFCBANK"],
        "Nifty IT Sector": ["CNXIT", "TCS", "INFY", "WIPRO", "TECHM"],
        "Nifty FMCG Sector": ["CNXFMCG", "ITC", "HINDUNILVR", "NESTLEIND"]
    }

# 2. Sidebar stock picker control panel
st.sidebar.header("🛠️ Manage Sector Stocks")
selected_sector = st.sidebar.selectbox("Select Sector", list(st.session_state.sectors_data.keys()))
current_stock_list = st.session_state.sectors_data[selected_sector]

st.sidebar.subheader("➕ Add New Stock")
new_stock = st.sidebar.text_input("Type NSE Symbol (e.g., SBIN)").strip().upper()
if st.sidebar.button("Add to Sector"):
    if new_stock and new_stock not in current_stock_list:
        st.session_state.sectors_data[selected_sector].append(new_stock)
        st.success(f"Added {new_stock}!")
        st.rerun()

st.sidebar.subheader("❌ Remove a Stock")
if len(current_stock_list) > 1:
    remove_stock = st.sidebar.selectbox("Choose stock to remove", current_stock_list)
    if st.sidebar.button("Remove from Sector"):
        st.session_state.sectors_data[selected_sector].remove(remove_stock)
        st.warning(f"Removed {remove_stock}!")
        st.rerun()

# 3. Fetching functions using live API data patterns
def fetch_live_api_data(symbol):
    """
    Template function to query live data feeds.
    Currently uses an open data stream to mock historical daily close structures.
    """
    try:
        # Mocking an open market feed framework. Replace URL with your actual API endpoint.
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol if '^' in symbol or '.' in symbol else symbol+'.NS'}?range=2y&interval=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10).json()
        
        result = response['chart']['result'][0]
        timestamps = result['timestamp']
        closes = result['indicators']['quote'][0]['close']
        highs = result['indicators']['quote'][0]['high']
        lows = result['indicators']['quote'][0]['low']
        
        df = pd.DataFrame({'Close': closes, 'High': highs, 'Low': lows}, index=pd.to_datetime(timestamps, unit='s'))
        return df.dropna()
    except Exception:
        return pd.DataFrame()

# Timeframes for returns matrix
time_frames = {
    "1 Day": 1, "3 Days": 3, "1 Week": 7, "1 Month": 30,
    "2 Months": 60, "3 Months": 90, "6 Months": 180, "1 Year": 365
}

matrix = []
with st.spinner("Fetching data from live API..."):
    for ticker in current_stock_list:
        # Handle index naming conventions smoothly
        api_symbol = "^NSEI" if ticker == "NIFTY" else ("^NSEBANK" if ticker == "BANKNIFTY" else ticker)
        df = fetch_live_api_data(api_symbol)
        
        if not df.empty:
            close_s = df['Close']
            current_close = float(close_s.iloc[-1])
            
            # Technical moving averages
            ma4 = round(float(close_s.rolling(4).mean().iloc[-1]), 2) if len(close_s) >= 4 else None
            ma20 = round(float(close_s.rolling(20).mean().iloc[-1]), 2) if len(close_s) >= 20 else None
            ma50 = round(float(close_s.rolling(50).mean().iloc[-1]), 2) if len(close_s) >= 50 else None
            
            # 52-Week High and Low parameters
            past_year_high = df['High'].iloc[-252:]
            past_year_low = df['Low'].iloc[-252:]
            high_52w = round(float(past_year_high.max()), 2)
            low_52w = round(float(past_year_low.min()), 2)
            
            row = {
                "Stock/Index": ticker,
                "Current Price": round(current_close, 2),
                "4 MA": ma4, "20 MA": ma20, "50 MA": ma50,
                "52W High": high_52w, "52W Low": low_52w
            }
            
            # Calculate timeframe movement
            for label, days in time_frames.items():
                target_date = close_s.index[-1] - timedelta(days=days)
                idx = close_s.index.get_indexer([target_date], method='pad')[0]
                past_price = float(close_s.iloc[idx])
                row[label] = round(((current_close - past_price) / past_price) * 100, 2)
                
            matrix.append(row)

# 4. Color Code Engine: Red background for negative numbers, Green background for positive numbers
def apply_color_formatting(val):
    if isinstance(val, (int, float)):
        if val < 0:
            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold;'  # Light Red Background / Dark Red Text
        elif val > 0:
            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold;'  # Light Green Background / Dark Green Text
    return ''

# Render the formatted layout
st.subheader(f"📊 Live Tracking Space: {selected_sector}")
if matrix:
    df_final = pd.DataFrame(matrix)
    
    # Define exact columns to format
    return_cols = list(time_frames.keys())
    
    # Bake structural styling directly into the dataframe wrapper
    styled_df = df_final.style.map(apply_color_formatting, subset=return_cols).format(precision=2)
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("Add standard symbols to populate the dataset display layout.")
