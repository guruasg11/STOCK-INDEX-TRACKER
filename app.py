import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Advanced Indian Market Tracker", layout="wide")
st.title("📈 Advanced Indian Market Sector Dashboard")

# 🏛️ Full NSE Autocomplete Dictionary Catalog 
NSE_CATALOG = {
    "HINDUNILVR (Hindustan Unilever Ltd)": "HINDUNILVR.NS",
    "RELIANCE (Reliance Industries Ltd)": "RELIANCE.NS",
    "TCS (Tata Consultancy Services Ltd)": "TCS.NS",
    "HDFCBANK (HDFC Bank Ltd)": "HDFCBANK.NS",
    "INFY (Infosys Ltd)": "INFY.NS",
    "SBIN (State Bank of India)": "SBIN.NS",
    "ICICIBANK (ICICI Bank Ltd)": "ICICIBANK.NS",
    "AXISBANK (Axis Bank Ltd)": "AXISBANK.NS",
    "WIPRO (Wipro Ltd)": "WIPRO.NS",
    "TECHM (Tech Mahindra Ltd)": "TECHM.NS",
    "ITC (ITC Ltd)": "ITC.NS",
    "NESTLEIND (Nestle India Ltd)": "NESTLEIND.NS",
    "BHARTIARTL (Bharti Airtel Ltd)": "BHARTIARTL.NS",
    "TATAMOTORS (Tata Motors Ltd)": "TATAMOTORS.NS",
    "NIFTY 50 INDEX": "^NSEI",
    "BANK NIFTY INDEX": "^NSEBANK",
    "NIFTY IT INDEX": "^CNXIT",
    "NIFTY FMCG INDEX": "^CNXFMCG"
}

# 1. Background memory setup (Session State)
if "sectors_data" not in st.session_state:
    st.session_state.sectors_data = {
        "Nifty 50": ["^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Bank Nifty": ["^NSEBANK", "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFCBANK.NS"],
        "Nifty IT Sector": ["^CNXIT", "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
        "Nifty FMCG Sector": ["^CNXFMCG", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS"]
    }

st.sidebar.header("⚙️ Configuration Console")

# 🆕 FEATURE 1: Add a Brand New Custom Sector Manually
st.sidebar.subheader("📁 Create New Sector")
new_sector_name = st.sidebar.text_input("New Sector Name (e.g., Pharma Sector)").strip()
if st.sidebar.button("Create Sector"):
    if new_sector_name and new_sector_name not in st.session_state.sectors_data:
        st.session_state.sectors_data[new_sector_name] = []
        st.success(f"Sector '{new_sector_name}' Created!")
        st.rerun()

# Sector Selector
selected_sector = st.sidebar.selectbox("Select Active Dashboard", list(st.session_state.sectors_data.keys()))
current_stock_list = st.session_state.sectors_data[selected_sector]

# 🆕 FEATURE 2: Add Stock via Interactive NSE Autocomplete Dropdown
st.sidebar.subheader("➕ Add Stock to Sector")
search_selection = st.sidebar.selectbox(
    "Type Company Name / Ticker:", 
    options=[""] + list(NSE_CATALOG.keys()),
    placeholder="Search (e.g., HUL, Reliance, Info...)"
)

if st.sidebar.button("Confirm and Add Stock"):
    if search_selection:
        ticker_to_add = NSE_CATALOG[search_selection]
        if ticker_to_add not in current_stock_list:
            st.session_state.sectors_data[selected_sector].append(ticker_to_add)
            st.success(f"Added {ticker_to_add} to {selected_sector}!")
            st.rerun()

# Remove a Stock
st.sidebar.subheader("❌ Remove a Stock")
if current_stock_list:
    remove_stock = st.sidebar.selectbox("Choose stock to remove", current_stock_list)
    if st.sidebar.button("Delete Stock"):
        st.session_state.sectors_data[selected_sector].remove(remove_stock)
        st.warning(f"Removed {remove_stock}!")
        st.rerun()

# 2. Live REST API Data Fetching Core
def fetch_live_api_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=2y&interval=1d"
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

if not current_stock_list:
    st.info("This sector folder is currently empty. Use the sidebar menu to add stock symbols.")
else:
    with st.spinner("Streaming real-time pricing and running technical screenings..."):
        for ticker in current_stock_list:
            df = fetch_live_api_data(ticker)
            
            if not df.empty:
                close_s = df['Close']
                current_close = float(close_s.iloc[-1])
                
                # Technical moving averages
                ma4 = round(float(close_s.rolling(4).mean().iloc[-1]), 2) if len(close_s) >= 4 else None
                ma20 = round(float(close_s.rolling(20).mean().iloc[-1]), 2) if len(close_s) >= 20 else None
                ma50 = round(float(close_s.rolling(50).mean().iloc[-1]), 2) if len(close_s) >= 50 else None
                
                # 52-Week High and Low parameters
                past_year_high = df['High'].iloc[-252:] if len(df) >= 252 else df['High']
                past_year_low = df['Low'].iloc[-252:] if len(df) >= 252 else df['Low']
                high_52w = round(float(past_year_high.max()), 2)
                low_52w = round(float(past_year_low.min()), 2)
                
                row = {
                    "Stock/Index": ticker,
                    "Current Price": round(current_close, 2),
                    "4 MA": ma4, "20 MA": ma20, "50 MA": ma50,
                    "52W High": high_52w, "52W Low": low_52w
                }
                
                # Calculate timeline change percent returns
                for label, days in time_frames.items():
                    target_date = close_s.index[-1] - timedelta(days=days)
                    idx = close_s.index.get_indexer([target_date], method='pad')[0]
                    past_price = float(close_s.iloc[idx])
                    row[label] = round(((current_close - past_price) / past_price) * 100, 2)
                    
                matrix.append(row)

# 3. 🆕 FEATURE 3: Complex Double-Layer Matrix Element Stylers
def apply_matrix_styles(df):
    """Applies cell returns colors and moving average rules simultaneously"""
    styled = df.style
    
    # Rule A: Green background for Positive Returns, Red background for Negative Returns
    return_cols = list(time_frames.keys())
    def style_returns(val):
        if isinstance(val, (int, float)):
            if val < 0: return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold;'
            elif val > 0: return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold;'
        return ''
    styled = styled.map(style_returns, subset=return_cols)
    
    # Rule B: Green text if Price > MA, Red text if Price < MA
    for idx in df.index:
        current_price = df.loc[idx, "Current Price"]
        for ma_col in ["4 MA", "20 MA", "50 MA"]:
            ma_val = df.loc[idx, ma_col]
            if pd.notna(ma_val) and pd.notna(current_price):
                color = "#2E7D32" if current_price > ma_val else "#C62828" # Dark Green vs Dark Red text
                styled = styled.set_properties(
                    **{'color': color, 'font-weight': 'bold'},
                    subset=pd.IndexSlice[[idx], [ma_col]]
                )
    return styled

# 4. Render Table
st.subheader(f"📊 Market Matrix View: {selected_sector}")
if matrix:
    df_raw = pd.DataFrame(matrix)
    styled_output = apply_matrix_styles(df_raw).format(precision=2)
    st.dataframe(styled_output, use_container_width=True, hide_index=True)
