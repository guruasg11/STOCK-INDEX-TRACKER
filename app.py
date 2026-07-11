import requests
import pandas as pd
import io

def fetch_nse_stock_list():
    """
    Fetches the latest list of equities listed on the NSE and returns a pandas DataFrame.
    """
    # 1. Define standard browser headers to bypass bot-protection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    # 2. Use a Session to persist cookies across requests
    session = requests.Session()
    session.headers.update(headers)
    
    # Base URL to generate cookies, and the target URL for the data
    base_url = "https://www.nseindia.com"
    csv_url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    
    try:
        # 3. Hit the base URL first to acquire the required session cookies
        session.get(base_url, timeout=15)
        
        # 4. Fetch the CSV using the authenticated session
        response = session.get(csv_url, timeout=15)
        response.raise_for_status()  
        
        # 5. Read the raw text response directly into a Pandas DataFrame
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean up column names by stripping trailing/leading spaces
        df.columns = df.columns.str.strip()
        
        return df

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None
    except pd.errors.EmptyDataError:
        print("Error: The fetched file is empty.")
        return None

# --- Execution ---
if __name__ == "__main__":
    nse_df = fetch_nse_stock_list()
    
    if nse_df is not None:
        print(f"Successfully loaded {len(nse_df)} stocks.")
        print("\nFirst 5 rows:")
        # Displaying key columns to verify the pull
        print(nse_df[['SYMBOL', 'NAME OF COMPANY', 'SERIES']].head())
