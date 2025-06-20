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

    now = datetime.now()

    # Map periods to date ranges
    if period and not (start_date and end_date):
        period_map = {
            "1D": (now - timedelta(days=1), now),
            "5D": (now - timedelta(days=5), now),
            "15D": (now - timedelta(days=15), now),
            "30D": (now - timedelta(days=30), now),
            "1M": (now - timedelta(days=30), now),
            "3M": (now - timedelta(days=90), now),
            "6M": (now - timedelta(days=180), now),
            "YTD": (datetime(now.year, 1, 1), now),
            "1Y": (now - timedelta(days=365), now),
            "2Y": (now - timedelta(days=730), now),
            "3Y": (now - timedelta(days=1095), now),
            "5Y": (now - timedelta(days=1825), now),
            "MAX": (datetime(1970, 1, 1), now)
        }
        if period not in period_map:
            raise ValueError(f"Invalid period: {period}")
        start_date, end_date = period_map[period]

    # === Correction starts here ===
    # Ensure end_date is not today or in the future (Yahoo may not have today's data yet)
    if end_date is not None:
        if end_date.date() >= now.date():
            end_date = now - timedelta(days=1)
            logger.info(f"Adjusted end_date to {end_date.date()} to avoid requesting future or incomplete data.")

    # Ensure start_date is before end_date
    if start_date is not None and end_date is not None and start_date >= end_date:
        raise ValueError(f"start_date {start_date.date()} must be before end_date {end_date.date()}")
    # === Correction ends here ===

    for attempt in range(1, retries + 1):
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date, interval="1d")

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
