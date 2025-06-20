import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def load_yfinance_data(symbol, period, start_date=None, end_date=None):
    """Load stock data from yfinance for the given symbol and period."""
    ticker = yf.Ticker(symbol)
    if period == "Custom":
        data = ticker.history(start=start_date, end=end_date)
    else:
        period_map = {
            "1D": "1d", "5D": "5d", "15D": "15d", "30D": "1mo",
            "1M": "1mo", "3M": "3mo", "6M": "6mo", "YTD": "ytd",
            "1Y": "1y", "2Y": "2y", "3Y": "3y", "5Y": "5y", "MAX": "max"
        }
        data = ticker.history(period=period_map.get(period, "1y"))
    if data.empty:
        raise ValueError("No data found for the given symbol/period")
    return data

def load_file_data(uploaded_file):
    """Load stock data from uploaded .csv or .xlsx file."""
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file, index_col=0, parse_dates=True)
    else:
        data = pd.read_excel(uploaded_file, index_col=0, parse_dates=True)
    
    required_columns = {'open', 'high', 'low', 'close', 'volume'}
    if not all(col.lower() in data.columns.str.lower() for col in required_columns):
        raise ValueError("File must contain columns: Open, High, Low, Close, Volume")
    return data
