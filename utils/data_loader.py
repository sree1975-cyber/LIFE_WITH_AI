import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
import streamlit as st
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)
def load_yfinance_data(symbol, period, start_date=None, end_date=None, retries=3, delay=2):
    """Load stock data from yfinance for the given symbol and period with retries."""
    logger.info(f"Loading data for {symbol}, period: {period}")
    
    for attempt in range(1, retries + 1):
        try:
            ticker = yf.Ticker(symbol)
            
            if period == "Custom":
                if start_date >= end_date:
                    raise ValueError("Start date must be before end date")
                if end_date > datetime.now():
                    raise ValueError("End date cannot be in the future")
                data = ticker.history(start=start_date, end=end_date, interval="1d")
            else:
                # Handle YTD explicitly with date range
                if period == "YTD":
                    start = datetime(datetime.now().year, 1, 1)
                    end = datetime.now()
                    data = ticker.history(start=start, end=end, interval="1d")
                else:
                    period_map = {
                        "1D": "1d", "5D": "5d", "15D": "15d", "30D": "1mo",
                        "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd",
                        "1Y": "1y", "2Y": "2y", "3Y": "3y", "5Y": "5y", "MAX": "max"
                    }
                    if period not in period_map:
                        raise ValueError(f"Invalid period: {period}")
                    data = ticker.history(period=period_map[period], interval="1d")
            
            if data.empty:
                # Check available data range
                try:
                    max_data = ticker.history(period="max", interval="1d")
                    if not max_data.empty:
                        start = max_data.index[0].date()
                        end = max_data.index[-1].date()
                        suggestions = "1M, Custom (post-2021)" if symbol == "CING" else "1M, YTD, Custom"
                        raise ValueError(
                            f"No data found for {symbol} in period {period}. "
                            f"Data is available from {start} to {end}. "
                            f"Try a period like {suggestions}."
                        )
                except Exception as e:
                    logger.warning(f"Failed to fetch max data for {symbol}: {str(e)}")
                raise ValueError(
                    f"No data found for {symbol} in period {period}. "
                    f"Try a period like 1M or Custom (post-2021 for CING), another symbol (e.g., AAPL), or use File Import."
                )
            
            # Select required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            data = data[[col for col in required_columns if col in data.columns]]
            # Normalize column names
            data.columns = [col.lower() for col in data.columns]
            logger.info(f"Successfully loaded data for {symbol}")
            return data
        
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {symbol}: {str(e)}")
            if attempt == retries:
                suggestions = "1M, Custom (post-2021)" if symbol == "CING" else "1M, YTD, Custom"
                raise ValueError(
                    f"Failed to load data for {symbol} in period {period} after {retries} attempts: {str(e)}. "
                    f"Try a period like {suggestions}, another symbol (e.g., AAPL), or use File Import."
                )
            time.sleep(delay * (2 ** (attempt - 1)))  # Exponential backoff: 2s, 4s, 8s
    
    raise ValueError(f"Failed to load data for {symbol} in period {period} after {retries} attempts")

def load_file_data(uploaded_file):
    """Load stock data from uploaded .csv or .xlsx file."""
    try:
        logger.info(f"Processing uploaded file: {uploaded_file.name}")
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file, index_col=0, parse_dates=True)
        else:
            data = pd.read_excel(uploaded_file, index_col=0, parse_dates=True)
        
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        if not all(col.lower() in data.columns.str.lower() for col in required_columns):
            raise ValueError("File must contain columns: Open, High, Low, Close, Volume")
        if data.empty:
            raise ValueError("Uploaded file contains no data")
        if not pd.api.types.is_datetime64_any_dtype(data.index):
            raise ValueError("File index must be a valid date")
        logger.info(f"Successfully processed file: {uploaded_file.name}")
        return data
    except Exception as e:
        logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")
