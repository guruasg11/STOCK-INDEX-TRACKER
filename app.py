import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Advanced Indian Market Tracker", layout="wide")
st.title("📈 Complete NSE Market Sector Dashboard")

# 📥 AUTOMATIC NSE MASTER LIST SCANNER
@st.cache_data(ttl=86400)  # Caches the list for 24 hours so it stays fast
def load_all_nse_symbols():
    """Fetches the official master list of all active stocks trading on the NSE"""
    try:
        # Download the complete CSV file directly from official market indices sources
        url = "https://niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            lines = response.text.split('\n')
            symbols = []
            for line in lines[1:]: # Skip the header row
                cols = line.split(',')
                if len(cols) > 1:
                    symbol = cols[1].strip().replace('"', '')
                    company = cols[0].strip().replace('"', '')
                    if symbol and company:
                        symbols.append(f"{symbol} ({company})")
            return sorted(symbols)
    except Exception:
        pass
    
    # Backup essential list if network timeout occurs during initialization
    return [
        "HINDUNILVR (Hindustan Unilever Ltd)", "RELIANCE (Reliance Industries Ltd)", 
        "TCS (Tata Consultancy Services Ltd)", "HDFCBANK (HDFC Bank Ltd)", 
        "INFY (Infosys Ltd)", "SBIN (State Bank of India)", "ICICIBANK (ICICI Bank Ltd)",
        "AXISBANK (Axis Bank Ltd)", "WIPRO (Wipro Ltd)", "TECHM (Tech Mahindra Ltd)", 
        "ITC (ITC Ltd)", "NESTLEIND (Nestle India Ltd)", "BHARTIARTL (Bharti Airtel Ltd)",
        "TATAMOTORS (Tata Motors Ltd)"
    ]

with st.spinner("Initializing master database of all NSE listed instruments..."):
    all_nse_stocks = load_all_nse_symbols()

# 1. Background memory setup (Session State)
if "sectors_data" not in st.session_state:
    st.session_state.sectors_data = {
        "Nifty 50": ["^NSEI", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Bank Nifty": ["^NSEBANK", "SBIN.NS", "AXISBANK.NS", "ICICIBANK.NS", "HDFCBANK.NS"],
        "Nifty IT Sector": ["^CNXIT", "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
        "Nifty FMCG Sector": ["^CNXFMCG", "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS"]
    }

st.sidebar.header("⚙️ Configuration Console")

# Create New Sector Manually
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

# Add Stock via Real-Time Dynamic NSE Catalog Selectbox
st.sidebar.subheader("➕ Add Stock to Sector")
search_selection = st.sidebar.selectbox(
    "Search All NSE Stocks:", 
    options=[""] + all_nse_stocks,
    placeholder="Type to search (e.g., HUL, Reliance, Tata...)"
)

if st.sidebar.button("Confirm and Add Stock"):
    if search_selection:
        # Extract the pure symbol handle from the dropdown string parentheses format
        pure_symbol = search_selection.split(" ")[0].strip()
        ticker_to_add = pure_symbol if "^" in pure_symbol else f"{pure_symbol}.NS"
        
        if ticker_to_add not in current_stock_list:
            st.session_state.sectors_data[selected_sector].append(ticker_to_add)
            st.success(f"Added {pure_symbol} to {selected_sector}!")
            st.rerun()

# Remove a Stock
st.sidebar.subheader("❌ Remove a Stock")
if current_stock_list:
    remove_stock = st.sidebar.selectbox("Choose stock to remove", current_stock_list)
    if st.sidebar.button("Delete Stock"):
        st.session_state.sectors_data[selected_sector].remove(remove_stock)
        st.warning(f"Removed {remove_stock}!")
        st.rerun()

# 2. Live Market API Core
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
    st.info("This sector folder is currently empty. Use the sidebar menu to search and add stock symbols.")
else:
    with st.spinner("Streaming data streams and calculating moving averages..."):
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
                    "Stock/Index": ticker.replace(".NS", ""),
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

# 3. ADVANCED DOUBLE-LAYER STRUCTURAL HIGHLIGHTER ENGINE
def apply_matrix_styles(df):
    styled = df.style
    
    # Rule A: Green background for Positive Returns, Red background for Negative Returns
    return_cols = list(time_frames.keys())
    def style_returns(val):
        if isinstance(val, (int, float)):
            if val < 0: return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold;'
            elif val > 0: return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold;'
        return ''
    styled = styled.map(style_returns, subset=return_cols)
    
    # Rule B: Highlight 52W High with soft green background and 52W Low with soft red background
    styled = styled.set_properties(**{'background-color': '#E8F5E9', 'color': '#2E7D32', 'font-weight': 'bold'}, subset=["52W High"])
    styled = styled.set_properties(**{'background-color': '#FFEBEE', 'color': '#C62828', 'font-weight': 'bold'}, subset=["52W Low"])
    
    # Rule C: Green text if Price > MA, Red text if Price < MA
    for idx in df.index:
        current_price = df.loc[idx, "Current Price"]
        for ma_col in ["4 MA", "20 MA", "50 MA"]:
            ma_val = df.loc[idx, ma_col]
            if pd.notna(ma_val) and pd.notna(current_price):
                color = "#2E7D32" if current_price > ma_val else "#C62828"
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
