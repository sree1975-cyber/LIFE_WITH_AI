import pandas as pd
import logging
import streamlit as st
from datetime import datetime
from utils.yfetch import fetch_yfinance_data
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)
def load_yfinance_data(symbol, period, start_date=None, end_date=None):
    """Load stock data from yfinance for the given symbol and period."""
    try:
        logger.info(f"Loading data for {symbol}, period: {period}")
        
        # Validate symbol
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
            if not info:
                raise ValueError(f"Symbol {symbol} not found or no metadata available")
        except Exception as e:
            logger.warning(f"Failed to fetch metadata for {symbol}: {str(e)}")
            raise ValueError(f"Invalid symbol {symbol} or no metadata available: {str(e)}")
        
        if period == "Custom":
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")
            if end_date > datetime.now():
                raise ValueError("End date cannot be in the future")
            data = fetch_yfinance_data(symbol, start_date=start_date, end_date=end_date)
        else:
            data = fetch_yfinance_data(symbol, period=period)
        
        if data.empty:
            try:
                max_data = fetch_yfinance_data(symbol, period="MAX")
                if not max_data.empty:
                    start = max_data.index[0].date()
                    end = max_data.index[-1].date()
                    suggestions = "1M, YTD, Custom (post-2021)" if symbol == "CING" else "1M, YTD, Custom"
                    raise ValueError(
                        f"No data found for {symbol} in period {period}. "
                        f"Data is available from {start} to {end}. "
                        f"Try a period like {suggestions}."
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch max data for {symbol}: {str(e)}")
            suggestions = "1M, YTD, Custom (post-2021)" if symbol == "CING" else "1M, YTD, Custom"
            raise ValueError(
                f"No data found for {symbol} in period {period}. "
                f"Try a period like {suggestions}, another symbol (e.g., AAPL), or use File Import."
            )
        
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data missing required columns: {required_columns}")
        
        data.columns = [col.lower() for col in data.columns]
        logger.info(f"Successfully loaded data for {symbol}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading data for {symbol}: {str(e)}")
        raise ValueError(f"Failed to load data for {symbol}: {str(e)}")

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
