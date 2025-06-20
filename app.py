import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import yfinance as yf
import logging
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from utils.data_loader import load_file_data
from utils.calculations import calculate_pl
from utils.visualizations import create_monthly_pl_table, create_candlestick_chart
from utils.indicators import calculate_indicators
from utils.strategies import apply_strategies
from utils.predictions import predict_prices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure requests session with retry strategy
session = requests.Session()
retry = Retry(
    total=5,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
yf.set_request_session(session)

# Set page configuration
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"
if 'period' not in st.session_state:
    st.session_state.period = "1y"
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

class DataLoader:
    def __init__(self):
        self.session = session
        
    def load_yfinance_data(self, symbol, period, start_date, end_date):
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}: Downloading data for {symbol}")
                
                if period:
                    data = yf.download(
                        tickers=symbol,
                        period=period,
                        interval="1d",
                        progress=False,
                        ignore_tz=True
                    )
                else:
                    data = yf.download(
                        tickers=symbol,
                        start=start_date,
                        end=end_date,
                        interval="1d",
                        progress=False,
                        ignore_tz=True
                    )
                
                if data is None or data.empty:
                    logger.warning(f"Attempt {attempt}: Empty data for {symbol}")
                    if attempt < max_retries:
                        sleep_time = backoff_factor ** attempt
                        time.sleep(sleep_time)
                        continue
                    return None
                
                # Clean up column names
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                data.columns = [col.lower() for col in data.columns]
                
                logger.info(f"Successfully downloaded data for {symbol}")
                return data
                
            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {symbol}: {str(e)}")
                if attempt < max_retries:
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                    continue
                logger.error(f"All attempts failed for {symbol}")
                return None
    
    def load_file_data(self, uploaded_file):
        return load_file_data(uploaded_file)

# Instantiate DataLoader
data_loader = DataLoader()

# Sidebar for data source selection
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Select Data Source", ["Yahoo Finance", "File Import"])

# Main UI
st.title("Stock Market Analysis Dashboard")

def display_data_info(data, source):
    """Display information about the loaded data"""
    st.info(f"""
    📋 **Data Information for {source}:**
    - Total Records: {len(data):,}
    - Date Range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}
    - Columns: {', '.join(data.columns.tolist())}
    """)

def process_stock_data(data):
    """Placeholder for data processing"""
    return data

def display_yfinance_interface():
    st.subheader("YFinance Data Retrieval")
    
    # Stock symbol input
    symbol = st.text_input(
        "Enter Stock Symbol",
        value=st.session_state.symbol,
        placeholder="e.g., AAPL, MSFT, GOOGL"
    ).upper()
    
    if symbol == "CING":
        st.info("CING data is available from December 2021. Use periods like 1mo or Custom (post-2021).")
    
    # Period selection
    col1, col2 = st.columns(2)
    
    with col1:
        period_type = st.selectbox(
            "Period Type",
            ["Predefined", "Custom Range"]
        )
    
    with col2:
        if period_type == "Predefined":
            period = st.selectbox(
                "Select Period",
                ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                index=5  # Default to 1y
            )
        else:
            st.write("Custom Date Range")
    
    if period_type == "Custom Range":
        col3, col4 = st.columns(2)
        with col3:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
        with col4:
            end_date = st.date_input("End Date", datetime.now())
        period = None
    else:
        start_date = None
        end_date = None
    
    if st.button("📥 Download Data", type="primary"):
        if symbol:
            if not re.match(r'^[A-Z0-9.-]+$', symbol):
                st.error("❌ Please enter a valid stock symbol (e.g., AAPL, CING)")
            elif period_type == "Custom Range" and (
                pd.Timestamp(start_date) >= pd.Timestamp(end_date) or 
                pd.Timestamp(end_date) > pd.Timestamp.now()
            ):
                st.error("❌ Start date must be before end date, and end date cannot be in the future")
            else:
                with st.spinner("Downloading data from YFinance..."):
                    try:
                        data = data_loader.load_yfinance_data(symbol, period, start_date, end_date)
                        if data is not None and not data.empty:
                            st.session_state.data = data
                            st.session_state.symbol = symbol
                            st.session_state.period = period if period else f"{start_date} to {end_date}"
                            
                            # Process data
                            st.session_state.processed_data = process_stock_data(data)
                            
                            st.success(f"✅ Data downloaded successfully for {symbol}")
                            
                            # Display data info
                            display_data_info(data, symbol)
                            st.rerun()
                        else:
                            suggestions = "1mo, Custom (post-2021)" if symbol == "CING" else "1mo, ytd, Custom"
                            st.error(f"❌ No data found for {symbol} in period {period if period else f'{start_date} to {end_date}'}. "
                                     f"Try a period like {suggestions}, another symbol (e.g., AAPL), or File Import.")
                    except Exception as e:
                        logger.error(f"Exception in yfinance download: {str(e)}")
                        st.error(f"❌ Error downloading data: {str(e)}")
        else:
            st.warning("⚠️ Please enter a stock symbol")

# Yahoo Finance UI
if data_source == "Yahoo Finance":
    col1, col2 = st.columns([2, 1])
    with col1:
        display_yfinance_interface()
    with col2:
        if st.button("🔄 Clear", key="clear", type="secondary"):
            st.session_state.data = None
            st.session_state.symbol = "AAPL"
            st.session_state.period = "1y"
            st.session_state.processed_data = None
            st.rerun()

# File Import UI
else:
    st.header("File Import")
    uploaded_file = st.file_uploader("Upload .csv or .xlsx file", type=["csv", "xlsx"])
    if uploaded_file:
        st.markdown("File data uploaded. Click 'Process' to load the data.")
        st.markdown("File must contain columns: Date (index), open, high, low, close, volume.")
    
    sample_data = pd.DataFrame({
        "date": ["2025-06-20", "2025-06-19"],
        "open": [2.0, 1.95],
        "high": [2.1, 2.0],
        "low": [1.9, 1.9],
        "close": [2.05, 2.0],
        "volume": [100000, 99999]
    }).set_index("date")
    csv = sample_data.to_csv()
    st.download_button("Download Sample CSV", data=csv, file_name="sample_stock_data.csv")
    
    if st.button("📤 Process", key="process_file", type="primary"):
        try:
            with st.spinner("Processing uploaded file..."):
                st.session_state.data = data_loader.load_file_data(uploaded_file)
                st.session_state.processed_data = process_stock_data(st.session_state.data)
                st.success("✅ File processed successfully")
                display_data_info(st.session_state.data, "Uploaded File")
                st.rerun()
        except ValueError as e:
            logger.error(f"Error processing file: {str(e)}")
            st.error(f"❌ Error processing file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing file: {str(e)}")
            st.error(f"❌ Unexpected error processing file: {str(e)}")
    
    if st.button("🔄 Clear", key="clear_file", type="secondary"):
        st.session_state.data = None
        st.session_state.processed_data = None
        st.rerun()

# Display Data and Analysis
if st.session_state.data is not None and not st.session_state.data.empty:
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    
    with st.expander("📈 Raw Data"):
        st.dataframe(st.session_state.data)
    
    if data_source == "Yahoo Finance":
        try:
            ticker = yf.Ticker(st.session_state.symbol)
            hist_data = ticker.history(period="1mo")
            if not hist_data.empty:
                st.info(f"Data available from {hist_data.index[0].date()} to {hist_data.index[-1].date()}")
            st.info(f"Period selected ranging from {st.session_state.data.index[0].date()} to {st.session_state.data.index[-1].date()}")
        except:
            st.warning("⚠️ Unable to fetch historical data range. Data may still be valid.")
    
    pl_data = calculate_pl(st.session_state.data)
    pl_data = calculate_indicators(pl_data)
    pl_data = apply_strategies(pl_data)
    
    with st.expander("💰 Profit and Loss Analysis"):
        st.dataframe(pl_data)
    
    monthly_pl = create_monthly_pl_table(pl_data, st.session_state.period)
    with st.expander("📅 Monthly P&L"):
        st.plotly_chart(monthly_pl, use_container_width=True)
    
    candlestick_chart = create_candlestick_chart(pl_data)
    with st.expander("📈 Candlestick Chart"):
        st.plotly_chart(candlestick_chart, use_container_width=True)
    
    with st.expander("🔮 Price Prediction"):
        horizon = st.selectbox("Prediction Horizon", ["1 Day", "5 Days", "1 Month"], key="horizon")
        horizon_map = {"1 Day": 1, "5 Days": 5, "1 Month": 30}
        try:
            pred_df, pred_chart = predict_prices(pl_data, horizon_map[horizon])
            st.dataframe(pred_df)
            st.plotly_chart(pred_chart, use_container_width=True)
        except Exception as e:
            logger.error(f"Error predicting prices: {str(e)}")
            st.error(f"❌ Prediction error: {str(e)}")

# Data Export
if st.session_state.data is not None and not st.session_state.data.empty:
    st.header("Export Data")
    export_format = st.selectbox("Export Format", ["CSV", "XLSX"], key="export_format")
    export_data = pl_data if 'pl_data' in locals() else st.session_state.data
    if export_format == "CSV":
        csv = export_data.to_csv(index=True)
        st.download_button(
            "Download Data", 
            csv, 
            f"stock_data_{st.session_state.symbol or 'file'}.csv", 
            "text/csv",
            key="download_csv"
        )
    else:
        import io
        output = io.BytesIO()
        export_data.to_excel(output, index=True)
        output.seek(0)
        st.download_button(
            "Download Data", 
            output, 
            f"stock_data_{st.session_state.symbol or 'file'}.xlsx", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_xlsx"
        )
