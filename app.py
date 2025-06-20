import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from utils.data_loader import load_yfinance_data, load_file_data
from utils.calculations import calculate_pl
from utils.visualizations import create_monthly_pl_table, create_candlestick_chart
from utils.indicators import calculate_indicators
from utils.strategies import apply_strategies
from utils.predictions import predict_prices

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

# Function to display data info
def display_data_info(data, symbol):
    if not data.empty:
        st.info(f"Data available for {symbol} from {data.index[0].date()} to {data.index[-1].date()}")

# Function for Yahoo Finance interface
def display_yfinance_interface():
    st.subheader("YFinance Data Retrieval")
    
    # Stock symbol input
    symbol = st.text_input(
        "Enter Stock Symbol",
        value=st.session_state.symbol,
        placeholder="e.g., AAPL, MSFT, GOOGL"
    ).upper()
    
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
                ["real-time", "1d", "5d", "1mo", "3mo", "6mo", "ytd", "1y", "2y", "3y", "5y", "max"],
                index=7  # Default to 1y
            )
        else:
            st.write("Custom Date Range")
    
    if period_type == "Custom Range":
        col3, col4 = st.columns(2)
        with col3:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
        with col4:
            end_date = st.date_input("End Date", datetime.now())
        period = "Custom"
    else:
        start_date = None
        end_date = None
    
    if st.button("📥 Download Data", type="primary"):
        if symbol and re.match(r'^[A-Z0-9.-]+$', symbol):
            with st.spinner("Downloading data from YFinance..."):
                try:
                    data = load_yfinance_data(symbol, period, start_date, end_date)
                    if data is not None and not data.empty:
                        st.session_state.data = data
                        st.session_state.symbol = symbol
                        st.session_state.period = period if period != "Custom" else f"{start_date} to {end_date}"
                        st.session_state.processed_data = calculate_pl(data)  # Assuming calculate_pl is equivalent to process_stock_data
                        st.success(f"✅ Data downloaded successfully for {symbol}")
                        display_data_info(data, symbol)
                        st.rerun()
                    else:
                        st.error(f"❌ No data found for {symbol} in period {period}. Try real-time, 1mo, ytd, or a shorter Custom period.")
                except Exception as e:
                    st.error(f"❌ Error downloading data: {str(e)}. Try real-time, 1mo, ytd, or check your network connection.")
        else:
            st.warning("⚠️ Please enter a valid stock symbol (e.g., AAPL, CING)")

# Sidebar for data source selection
st.sidebar.header("Data Source")
data_source = st.sidebar.radio("Select Data Source", ["Yahoo Finance", "File Import"])

# Main UI
st.title("Stock Market Analysis Dashboard")

# Yahoo Finance UI
if data_source == "Yahoo Finance":
    display_yfinance_interface()

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
                st.session_state.processed_data = calculate_pl(st.session_state.data)
                st.session_state.symbol = uploaded_file.name.split('.')[0]
                st.session_state.period = "Uploaded File"
                st.success("File data loaded successfully")
                display_data_info(st.session_state.data, st.session_state.symbol)
                st.rerun()
            except ValueError as e:
                st.error(f"Error processing file: {str(e)}")
            except Exception as e:
                st.error(f"Unexpected error processing file: {str(e)}")
    
    if st.button("Clear", key="clear_file"):
        st.session_state.data = None
        st.session_state.processed_data = None
        st.session_state.symbol = "AAPL"
        st.session_state.period = "1y"
        st.rerun()

# Display Data and Analysis
if st.session_state.data is not None and not st.session_state.data.empty:
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    
    with st.expander("View Raw Data"):
        st.dataframe(st.session_state.data)
    
    if data_source == "Yahoo Finance":
        st.info(f"Selected period: {st.session_state.period}")
    
    pl_data = st.session_state.processed_data or calculate_pl(st.session_state.data)
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
    export_data = st.session_state.processed_data if st.session_state.processed_data is not None else st.session_state.data
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
