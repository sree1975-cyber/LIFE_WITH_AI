import pandas as pd
import yfinance as yf
import logging
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)
def fetch_yfinance_data(stock_symbol, start_date=None, end_date=None, period="max", interval="1d"):
    """Fetch stock data from yfinance for the given symbol and period or date range."""
    try:
        logger.info(f"Fetching data for {stock_symbol}, period: {period}, start: {start_date}, end: {end_date}")
        if period == "real-time":
            data = yf.download(stock_symbol, period="1d", interval="1m")
        elif period == "max":
            data = yf.download(stock_symbol, period="max", interval=interval)
        else:
            if start_date is None or end_date is None:
                end_date = pd.to_datetime('today')
                period_days = {
                    "1D": 1,
                    "5D": 5,
                    "1M": 30,
                    "YTD": (pd.to_datetime('today') - pd.Timestamp(year=pd.to_datetime('today').year, month=1, day=1)).days,
                    "1Y": 365,
                    "5Y": 1825,
                    "10Y": 3650
                }.get(period, 365)
                start_date = end_date - pd.Timedelta(days=period_days)
            data = yf.download(stock_symbol, start=start_date, end=end_date, interval=interval)
        if data.empty:
            st.error(f"No data found for {stock_symbol} in period {period}.")
            logger.warning(f"No data returned for {stock_symbol} from {start_date} to {end_date}")
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()
        if data.index.duplicated().any():
            st.warning(f"Duplicate indices found for {stock_symbol}. Dropping duplicates.")
            data = data[~data.index.duplicated(keep='first')]
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        logger.info(f"Successfully fetched data for {stock_symbol}")
        return data
    except Exception as e:
        st.error(f"Error fetching data for {stock_symbol}: {str(e)}")
        logger.error(f"fetch_yfinance_data error for {stock_symbol}: {str(e)}")
        return pd.DataFrame()
