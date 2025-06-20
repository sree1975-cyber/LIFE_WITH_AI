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
def fetch_yfinance_data(symbol, start_date=None, end_date=None, period=None, interval="1d", retries=5, delay=3):
    """Fetch stock data from yfinance for the given symbol and period or date range."""
    logger.info(f"Fetching data for {symbol}, period: {period}, start: {start_date}, end: {end_date}, interval: {interval}")
    
    # Normalize period names to match both app.py and display_yfinance_interface
    period_map = {
        "real-time": ("1d", "1m"),
        "1D": ("1d", "1d"), "1d": ("1d", "1d"),
        "5D": ("5d", "1d"), "5d": ("5d", "1d"),
        "15D": ("15d", "1d"), "15d": ("15d", "1d"),
        "30D": ("30d", "1d"), "30d": ("30d", "1d"),
        "1M": ("1mo", "1d"), "1mo": ("1mo", "1d"),
        "3M": ("3mo", "1d"), "3mo": ("3mo", "1d"),
        "6M": ("6mo", "1d"), "6mo": ("6mo", "1d"),
        "YTD": ("ytd", "1d"), "ytd": ("ytd", "1d"),
        "1Y": ("1y", "1d"), "1y": ("1y", "1d"),
        "2Y": ("2y", "1d"), "2y": ("2y", "1d"),
        "3Y": ("3y", "1d"), "3y": ("3y", "1d"),
        "5Y": ("5y", "1d"), "5y": ("5y", "1d"),
        "10y": ("10y", "1d"),
        "MAX": ("max", "1d"), "max": ("max", "1d")
    }
    
    # Map period to yfinance-compatible period and interval
    if period and period in period_map and not (start_date and end_date):
        yf_period, yf_interval = period_map[period]
        interval = yf_interval
    elif period == "Custom" or (start_date and end_date):
        yf_period = None
    else:
        raise ValueError(f"Invalid period: {period}")
    
    start_date = pd.Timestamp(start_date) if start_date else None
    end_date = pd.Timestamp(end_date) if end_date else pd.to_datetime('today')
    
    for attempt in range(1, retries + 1):
        try:
            if yf_period == "1d" and interval == "1m":
                data = yf.download(symbol, period="1d", interval="1m", progress=False)
            elif yf_period:
                data = yf.download(symbol, period=yf_period, interval=interval, progress=False)
            else:
                data = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
            
            if data.empty:
                logger.warning(f"No data returned for {symbol} on attempt {attempt} (period: {period}, start: {start_date}, end: {end_date})")
                if period not in ["1D", "1d", "1M", "1mo", "real-time"]:
                    logger.info(f"Falling back to 1y for {symbol}")
                    data = yf.download(symbol, period="1y", interval="1d", progress=False)
                if data.empty:
                    logger.info(f"Fallback to 1mo for {symbol}")
                    data = yf.download(symbol, period="1mo", interval="1d", progress=False)
                if data.empty:
                    st.error(f"No data found for {symbol} from {start_date.date() if start_date else 'start'} to {end_date.date()}. Try a shorter period or check network.")
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
                st.error(f"Failed to fetch data for {symbol} after {retries} attempts: {str(e)}. Try a shorter period or check network.")
                return pd.DataFrame()
            time.sleep(delay * (2 ** (attempt - 1)))
    
    return pd.DataFrame()
