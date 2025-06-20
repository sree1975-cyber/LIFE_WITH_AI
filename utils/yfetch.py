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
def fetch_yfinance_data(symbol, start_date=None, end_date=None, period=None, interval="1d", retries=3, delay=2):
    """Fetch stock data from yfinance for the given symbol and period or date range."""
    logger.info(f"Fetching data for {symbol}, period: {period}, start: {start_date}, end: {end_date}")
    
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
        if period not in period_map:
            raise ValueError(f"Invalid period: {period}")
        if period == "MAX":
            start_date = None
        else:
            start_date = end_date - pd.Timedelta(days=period_map[period])
    
    start_date = pd.Timestamp(start_date) if start_date else None
    end_date = pd.Timestamp(end_date) if end_date else pd.to_datetime('today')
    
    for attempt in range(1, retries + 1):
        try:
            if period == "MAX":
                data = yf.download(symbol, period="max", interval=interval, auto_adjust=True, prepost=False)
            else:
                data = yf.download(symbol, start=start_date, end=end_date, interval=interval, auto_adjust=True, prepost=False)
            
            if data.empty:
                # Try fallback periods
                for fallback_period in ["1mo", "5d"]:
                    if period and period not in ["1D", "5D", "1M"]:
                        logger.info(f"Falling back to {fallback_period} for {symbol}")
                        data = yf.download(symbol, period=fallback_period, interval=interval, auto_adjust=True, prepost=False)
                        if not data.empty:
                            break
                if data.empty:
                    raise ValueError(f"No data returned for {symbol} from {start_date.date() if start_date else 'start'} to {end_date.date()}")
            
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if not data.index.is_monotonic_increasing:
                data = data.sort_index()
            if data.index.duplicated().any():
                logger.warning(f"Duplicate indices found for {symbol}. Dropping duplicates.")
                data = data[~data.index.duplicated(keep='first')]
            if data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data = data[[col for col in required_columns if col in data.columns]]
            data.columns = [col.lower() for col in data.columns]
            
            logger.info(f"Successfully fetched data for {symbol} from {start_date.date() if start_date else 'start'} to {end_date.date()}")
            return data
        
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {symbol}: {str(e)}")
            if attempt == retries:
                raise ValueError(f"Failed to fetch data for {symbol} after {retries} attempts: {str(e)}")
            time.sleep(delay * (2 ** (attempt - 1)))
    
    raise ValueError(f"Failed to fetch data for {symbol} after {retries} attempts")
