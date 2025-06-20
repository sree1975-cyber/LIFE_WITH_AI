import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_yfinance_data(symbol, period, start_date=None, end_date=None, retries=3, delay=2):
    """Load stock data from yfinance for the given symbol and period with retry mechanism."""
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt} to load data for {symbol}, period: {period}")
            ticker = yf.Ticker(symbol)
            # Validate ticker
            try:
                info = ticker.info
                if not info or 'symbol' not in info:
                    raise ValueError(f"Invalid stock symbol: {symbol}")
            except json.decoder.JSONDecodeError as e:
                raise ValueError(f"Failed to validate symbol {symbol}: JSON decode error ({str(e)})")
            
            if period == "Custom":
                if start_date >= end_date:
                    raise ValueError("Start date must be before end date")
                if end_date > datetime.now():
                    raise ValueError("End date cannot be in the future")
                data = ticker.history(start=start_date, end=end_date, raise_errors=True)
            else:
                period_map = {
                    "1D": "1d", "5D": "5d", "15D": "15d", "30D": "1mo",
                    "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd",
                    "1Y": "1y", "2Y": "2y", "3Y": "3y", "5Y": "5y", "MAX": "max"
                }
                if period not in period_map:
                    raise ValueError(f"Invalid period: {period}")
                data = ticker.history(period=period_map[period], raise_errors=True)
            
            if data.empty:
                raise ValueError(f"No data found for {symbol} in the specified period")
            logger.info(f"Successfully loaded data for {symbol}")
            return data
        
        except json.decoder.JSONDecodeError as e:
            logger.warning(f"JSON decode error for {symbol} on attempt {attempt}: {str(e)}")
            if attempt == retries:
                raise ValueError(f"Failed to load data for {symbol} after {retries} attempts: JSON decode error. Yahoo Finance API may be unavailable.")
        except Exception as e:
            logger.warning(f"Error loading data for {symbol} on attempt {attempt}: {str(e)}")
            if attempt == retries:
                raise ValueError(f"Failed to load data for {symbol} after {retries} attempts: {str(e)}")
        
        time.sleep(delay)  # Delay before retry
    
    raise ValueError(f"Failed to load data for {symbol} after {retries} attempts")

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
