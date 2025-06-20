import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import yfinance as yf
import logging
from utils.data_loader import load_file_data
from utils.calculations import calculate_pl
from utils.visualizations import create_monthly_pl_table, create_candlestick_chart
from utils.indicators import calculate_indicators
from utils.strategies import apply_strategies
from utils.predictions import predict_prices

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"
if 'period' not in st.session_state:
    st.session_state.period = "1y"
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now() - timedelta(days=365)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()
if 'is_custom_symbol' not in st.session_state:
    st.session_state.is_custom_symbol = False

# Sidebar for data source selection
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Select Data Source", ["Yahoo Finance", "File Import"])

# Main UI
st.title("Stock Market Analysis Dashboard")

# Yahoo Finance UI
if data_source == "Yahoo Finance":
    st.header("Yahoo Finance Data")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbols = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "CING"]
        symbol_selection = st.selectbox(
            "Select or Enter Symbol",
            options=symbols + ["Custom"],
            index=symbols.index(st.session_state.symbol) if st.session_state.symbol in symbols else len(symbols),
            key="symbol_select"
        )
        
        if symbol_selection == "Custom":
            st.session_state.is_custom_symbol = True
            st.session_state.symbol = st.text_input(
                "Enter Stock Symbol (e.g., AAPL, CING)",
                value=st.session_state.symbol if st.session_state.is_custom_symbol else "",
                key="custom_symbol",
                placeholder="e.g., AAPL, MSFT, GOOGL"
            ).upper()
        else:
            st.session_state.is_custom_symbol = False
            st.session_state.symbol = symbol_selection
        
        if st.session_state.symbol == "CING":
            st.info("CING data is available from December 2021. Use periods like 1mo or Custom (post-2021).")
    
    with col2:
        period_type = st.selectbox(
            "Period Type",
            ["Predefined", "Custom Range"],
            key="period_type_select"
        )
        
        if period_type == "Predefined":
            periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"]
            st.session_state.period = st.selectbox(
                "Select Period",
                periods,
                index=periods.index(st.session_state.period) if st.session_state.period in periods else 5,
                key="period_select"
            )
        else:
            st.session_state.period = "Custom"
    
    if period_type == "Custom Range":
        col3, col4 = st.columns(2)
        with col3:
            start_date_input = st.date_input(
                "Start Date",
                value=st.session_state.start_date,
                key="start_date"
            )
        with col4:
            end_date_input = st.date_input(
                "End Date",
                value=st.session_state.end_date,
                key="end_date"
            )
    
    col5, col6 = st.columns([2, 1])
    with col5:
        if st.button("📥 Submit", key="submit", type="primary"):
            if not st.session_state.symbol or not re.match(r'^[A-Z0-9.-]+$', st.session_state.symbol):
                st.error("Please enter a valid stock symbol (e.g., AAPL, CING)")
            elif st.session_state.period == "Custom" and (
                pd.Timestamp(start_date_input) >= pd.Timestamp(end_date_input) or 
                pd.Timestamp(end_date_input) > pd.Timestamp.now()
            ):
                st.error("Start date must be before end date, and end date cannot be in the future")
            else:
                with st.spinner("Downloading data from Yahoo Finance..."):
                    try:
                        logger.info(f"Attempting to download data for {st.session_state.symbol}, period: {st.session_state.period}")
                        if st.session_state.period == "Custom":
                            st.session_state.start_date = start_date_input
                            st.session_state.end_date = end_date_input
                            data = yf.download(
                                st.session_state.symbol,
                                start=start_date_input,
                                end=end_date_input,
                                interval="1d",
                                progress=False
                            )
                        else:
                            data = yf.download(
                                st.session_state.symbol,
                                period=st.session_state.period,
                                interval="1d",
                                progress=False
                            )
                        
                        if data.empty:
                            logger.warning(f"Empty data returned for {st.session_state.symbol}, period: {st.session_state.period}")
                            suggestions = "1mo, Custom (post-2021)" if st.session_state.symbol == "CING" else "1mo, ytd, Custom"
                            try:
                                # Fallback to 1mo if shorter periods fail
                                if st.session_state.period in ["1d", "5d"]:
                                    logger.info(f"Falling back to 1mo for {st.session_state.symbol}")
                                    data = yf.download(
                                        st.session_state.symbol,
                                        period="1mo",
                                        interval="1d",
                                        progress=False
                                    )
                                if data.empty:
                                    max_data = yf.download(st.session_state.symbol, period="max", progress=False)
                                    if not max_data.empty:
                                        start = max_data.index[0].date()
                                        end = max_data.index[-1].date()
                                        st.error(
                                            f"No data found for {st.session_state.symbol} in period {st.session_state.period}. "
                                            f"Data is available from {start} Vaultto {end}. Try a period like {suggestions}."
                                        )
                                    else:
                                        st.error(
                                            f"No data found for Anastasiafor {st.session_state.symbol} in period {st.session_state.period}. "
                                            f"Try a period like {suggestions}, another symbol (e.g., AAPL), or File Import."
                                        )
                                else:
                                    st.session_state.data = data
                                    st.success(f"✅ Fallback data (1mo) downloaded successfully for {st.session_state.symbol}")
                            except Exception as e:
                                logger.error(f"Error fetching max data for {st.session_state.symbol}: {str(e)}")
                                st.error(
                                    f"No data found for {st.session_state.symbol} in period {st.session_state.period}. "
                                    f"Try a period like {suggestions}, another symbol (e.g., AAPL), or File Import."
                                )
                        else:
                            if isinstance(data.columns, pd.MultiIndex):
                                data.columns = data.columns.get_level_values(0)
                            if not data.index.is_monotonic_increasing:
                                data = data.sort_index()
                            if data.index.duplicated().any():
                                logger.warning(f"Duplicate indices found for {st.session_state.symbol}. Dropping duplicates.")
                                data = data[~data.index.duplicated(keep='first')]
                            if data.index.tz is not None:
                                data.index = data.index.tz_localize(None)
                            
                            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                            data = data[[col for col in required_columns if col in data.columns]]
                            data.columns = [col.lower() for col in data.columns]
                            
                            st.session_state.data = data
                            logger.info(f"Successfully downloaded data for {st.session_state.symbol}")
                            st.success(f"✅ Data downloaded successfully for {st.session_state.symbol}")
                    except Exception as e:
                        logger.error(f"Error downloading data for {st.session_state.symbol}: {str(e)}")
                        st.error(f"❌ Error downloading data: {str(e)}")
    
    with col6:
        if st.button("Clear", key="clear"):
            st.session_state.data = None
            st.session_state.symbol = "AAPL"
            st.session_state.period = "1y"
            st.session_state.start_date = datetime.now() - timedelta(days=365)
            st.session_state.end_date = datetime.now()
            st.session_state.is_custom_symbol = False
            st.rerun()

# File Import UI
else:
    st.header("File Import")
    uploaded_file = st.file_uploader("Upload .csv or .xlsx file", type=["csv", "xlsx"])
    st.markdown("File must contain columns: Date (index), Open, High, Low, Close, Volume.")
    
    sample_data = pd.DataFrame({
        "Date": ["2025-06-20", "2025-06-19"],
        "Open": [2.0, 1.95],
        "High": [2.1, 2.0],
        "Low": [1.9, 1.9],
        "Close": [2.05, 2.0],
        "Volume": [100000, 120000]
    }).set_index("Date")
    csv = sample_data.to_csv()
    st.download_button("Download Sample CSV", data=csv, file_name="sample_stock_data.csv")
    
    if st.button("Process", key="process"):
        if uploaded_file:
            try:
                st.session_state.data = load_file_data(uploaded_file)
                st.success("File data loaded successfully")
            except ValueError as e:
                st.error(f"Error processing file: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error processing file: {str(e)}")
    
    if st.button("Clear", key="clear_file"):
        st.session_state.data = None
        st.rerun()

# Display Data and Analysis
if st.session_state.data is not None and not st.session_state.data.empty:
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    
    with st.expander("View Raw Data"):
        st.dataframe(st.session_state.data)
    
    if data_source == "Yahoo Finance":
        try:
            ticker = yf.Ticker(st.session_state.symbol)
            hist_data = ticker.history(period="max")
            if not hist_data.empty:
                st.info(f"Total historical data available from {hist_data.index[0].date()} to {hist_data.index[-1].date()}")
            st.info(f"Selected period data from {st.session_state.data.index[0].date()} to {st.session_state.data.index[-1].date()}")
        except:
            st.warning("Unable to fetch historical data range. Data may still be valid.")

    pl_data = calculate_pl(st.session_state.data)
    pl_data = calculate_indicators(pl_data)
    pl_data = apply_strategies(pl_data)
    
    with st.expander("Profit and Loss Analysis"):
        st.dataframe(pl_data)
    
    monthly_pl = create_monthly_pl_table(pl_data, st.session_state.period)
    with st.expander("Monthly P/L Comparison"):
        st.plotly_chart(monthly_pl, use_container_width=True)
    
    candlestick_chart = create_candlestick_chart(pl_data)
    with st.expander("Candlestick Chart"):
        st.plotly_chart(candlestick_chart, use_container_width=True)
    
    with st.expander("Price Prediction"):
        horizon = st.selectbox("Prediction Horizon", ["1 Day", "5 Days", "1 Month"], key="horizon")
        horizon_map = {"1 Day": 1, "5 Days": 5, "1 Month": 30}
        try:
            pred_df, pred_chart = predict_prices(pl_data, horizon_map[horizon])
            st.dataframe(pred_df)
            st.plotly_chart(pred_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error in prediction: {str(e)}")

# Export Data
if st.session_state.data is not None and not st.session_state.data.empty:
    st.header("Export Data")
    export_format = st.selectbox("Select Export Format", ["CSV", "XLSX"], key="export_format")
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
