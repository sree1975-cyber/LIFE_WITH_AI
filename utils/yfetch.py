import pandas as pd
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_yfinance_data(symbol, start_date=None, end_date=None, period=None, retries=3, delay=2):
    """Fetch stock data from yfinance for the given symbol and period or date range."""
    logger.info(f"Fetching data for {symbol}, period: {period}, start: {start_date}, end: {end_date}")
    
    # Map periods to date ranges
    if period and not (start_date and end_date):
        now = datetime.now()
        period_map = {
            "1D": (now - timedelta(days=1), now),
            "5D": (now - timedelta(days=5), now),
            "15D": (now - timedelta(days=15), now),
            "30D": (now - timedelta(days=30), now),
            "1M": (now - timedelta(days=30), now),
            "3M": (now - timedelta(days=90), now),
            "6M": (now - timedelta(days=180), now),
            "YTD": (datetime(now.year, 1, 1), now),
            "1Y": (now - timedelta(days=365), now + timedelta(days=1)),  # Include today
            "2Y": (now - timedelta(days=730), now + timedelta(days=1)),
            "3Y": (now - timedelta(days=1095), now + timedelta(days=1)),
            "5Y": (now - timedelta(days=1825), now + timedelta(days=1)),
            "MAX": (datetime(1970, 1, 1), now + timedelta(days=1))
        }
        if period not in period_map:
            raise ValueError(f"Invalid period: {period}")
        start_date, end_date = period_map[period]
    
    # Ensure dates are datetime
    start_date = pd.Timestamp(start_date).to_pydatetime()
    end_date = pd.Timestamp(end_date).to_pydatetime()
    
    for attempt in range(1, retries + 1):
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date, interval="1d")
            
            if df.empty:
                # Fallback to shorter period if possible
                if period and period not in ["1D", "1M"]:
                    logger.info(f"Falling back to 1M for {symbol}")
                    fallback_df = stock.history(period="1mo", interval="1d")
                    if not fallback_df.empty:
                        df = fallback_df
                if df.empty:
                    raise ValueError(f"No data returned for {symbol} from {start_date.date()} to {end_date.date()}")
            
            # Select required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in required_columns if col in df.columns]]
            
            # Normalize column names
            df.columns = [col.lower() for col in df.columns]
            
            logger.info(f"Successfully fetched data for {symbol} from {start_date.date()} to {end_date.date()}")
            return df
        
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {symbol}: {str(e)}")
            if attempt == retries:
                raise ValueError(f"Failed to fetch data for {symbol} after {retries} attempts: {str(e)}")
            time.sleep(delay * (2 ** (attempt - 1)))  # Exponential backoff: 2s, 4s, 8s
    
    raise ValueError(f"Failed to fetch data for {symbol} after {retries} attempts")
