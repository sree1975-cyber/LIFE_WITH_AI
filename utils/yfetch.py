import pandas as pd
import yfinance as yf
import logging
import time
import streamlit as st
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)
def fetch_yfinance_data(symbol, start_date=None, end_date=None, period=None, interval="1d", retries=5, delay=5):
    """Fetch stock data from yfinance for the given symbol and period or date range."""
    logger.info(f"Fetching data for {symbol}, period: {period}, start: {start_date}, end: {end_date}, interval: {interval}")
    
    # Validate interval based on period
    if period in ["1D", "5D"] and interval not in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d"]:
        interval = "1d"
        logger.info(f"Adjusted interval to '1d' for period {period}")
    
    # Map periods to days for date range calculation
    if period and not (start_date and end_date):
        end_date = pd.to_datetime('today')
        period_map = {
            "1D": 1,
            "5D": 5,
            "15D": 15,
            "30D": 30,
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "YTD": (pd.to_datetime('today') - pd.Timestamp(year=pd.to_datetime('today').year, month=1, day=1)).days,
            "1Y": 365,
            "2Y": 730,
            "3Y": 1095,
            "5Y": 1825,
            "MAX": None
        }
        if period not in period_map and period != "real-time":
            raise ValueError(f"Invalid period: {period}")
        if period == "MAX":
            start_date = None
        elif period == "real-time":
            interval = "1m"  # Force 1-minute interval for real-time
            start_date = end_date - pd.Timedelta(days=1)
        else:
            start_date = end_date - pd.Timedelta(days=period_map[period])
    
    start_date = pd.Timestamp(start_date) if start_date else None
    end_date = pd.Timestamp(end_date) if end_date else pd.to_datetime('today')
    
    for attempt in range(1, retries + 1):
        try:
            if period == "real-time":
                data = yf.download(symbol, period="1d", interval="1m")
            elif period == "MAX":
                data = yf.download(symbol, period="max", interval=interval)
            else:
                data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                logger.warning(f"No data returned for {symbol} on attempt {attempt}")
                if period not in ["1D", "1M", "real-time"]:
                    logger.info(f"Falling back to 1M for {symbol}")
                    data = yf.download(symbol, period="1mo", interval="1d")
                if data.empty:
                    st.error(f"No data found for {symbol} from {start_date.date() if start_date else 'start'} to {end_date.date()}.")
                    return pd.DataFrame()
            
            # Handle multi-index columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            # Sort index and remove duplicates
            if not data.index.is_monotonic_increasing:
                data = data.sort_index()
            if data.index.duplicated().any():
                logger.warning(f"Duplicate indices found for {symbol}. Dropping duplicates.")
                data = data[~data.index.duplicated(keep='first')]
            # Remove timezone information
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            
            # Ensure required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data = data[[col for col in required_columns if col in data.columns]]
            data.columns = [col.lower() for col in data.columns]
            
            logger.info(f"Successfully fetched data for {symbol} from {start_date.date() if start_date else 'start'} to {end_date.date()}")
            return data
        
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {symbol}: {str(e)}")
            if attempt == retries:
                st.error(f"Failed to fetch data for {symbol} after {retries} attempts: {str(e)}")
                return pd.DataFrame()
            time.sleep(delay * (2 ** (attempt - 1)))
    
    return pd.DataFrame()
