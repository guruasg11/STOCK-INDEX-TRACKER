import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Indian Sector Tracker", layout="wide")
st.title("📈 Indian Market Sector Returns")

# 1. Choose the Indian sectors to track
sectors = {
    "Nifty 50 (Main Index)": "^NSEI",
    "Nifty Bank (Banking)": "^NSEBANK",
    "Nifty IT (Software)": "^CNXIT",
    "Nifty FMCG (Daily Goods)": "^CNXFMCG",
    "Nifty Pharma (Healthcare)": "^CNXPHARMA",
    "Nifty Auto (Vehicles)": "^CNXAUTO"
}

# 2. Set up the time frames
time_frames = {
    "1 Day": 1,
    "1 Week": 7,
    "1 Month": 30,
    "3 Months": 90,
    "6 Months": 180,
    "1 Year": 365
}

# 3. Fetch data and calculate percentages
matrix = []
today = datetime.today()

for name, ticker in sectors.items():
    # Download past data from the free engine
    df = yf.download(ticker, start=(today - timedelta(days=500)).strftime('%Y-%m-%d'), end=today.strftime('%Y-%m-%d'), progress=False)
    if not df.empty:
        current_close = float(df['Close'].iloc[-1])
        row = {"Sector Name": name, "Current Value": round(current_close, 2)}
        
        for label, days in time_frames.items():
            target_date = df.index[-1] - timedelta(days=days)
            idx = df.index.get_indexer([target_date], method='pad')[0]
            past_price = float(df['Close'].iloc[idx])
            
            # Simple math: ((New Price - Old Price) / Old Price) * 100
            row[label] = round(((current_close - past_price) / past_price) * 100, 2)
        matrix.append(row)

# 4. Show it on your website as a clean table
df_final = pd.DataFrame(matrix)
st.dataframe(df_final, use_container_width=True, hide_index=True)
