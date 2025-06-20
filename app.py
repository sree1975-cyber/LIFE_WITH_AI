import streamlit as st
import pandas as pd
import re
from utils.data_loader import load_file_data, load_yfinance_data
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
    st.session_state.period = "1Y"
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
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
                key="custom_symbol"
            )
        else:
            st.session_state.is_custom_symbol = False
            st.session_state.symbol = symbol_selection
        
        if st.session_state.symbol == "CING":
            st.info("CING data is available from December 2021. Use periods like 1M or Custom (post-2021).")
    
    with col2:
        periods = ["1D", "5D", "15D", "30D", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y", "MAX", "Custom"]
        st.session_state.period = st.selectbox("Select Period", periods, 
                                               index=periods.index(st.session_state.period),
                                               key="period_select")
    
    if st.session_state.period == "Custom":
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.start_date = st.date_input(
                "Start Date", 
                value=pd.to_datetime("today") - pd.Timedelta(days=365),
                key="start_date"
            )
        with col4:
            st.session_state.end_date = st.date_input(
                "End Date", 
                value=pd.to_datetime("today"),
                key="end_date"
            )
    
    col5, col6 = st.columns([2, 1])
    with col5:
        if st.button("Submit", key="submit"):
            if not st.session_state.symbol or not re.match(r'^[A-Z0-9.-]+$', st.session_state.symbol):
                st.error("Please enter a valid stock symbol (e.g., AAPL, CING)")
            elif st.session_state.period == "Custom" and (
                pd.Timestamp(st.session_state.start_date) >= pd.Timestamp(st.session_state.end_date) or 
                pd.Timestamp(st.session_state.end_date) > pd.Timestamp.now()
            ):
                st.error("Start date must be before end date, and end date cannot be in the future")
            else:
                with st.spinner("Loading data from Yahoo Finance..."):
                    try:
                        if st.session_state.period == "Custom":
                            st.session_state.data = load_yfinance_data(
                                st.session_state.symbol, 
                                st.session_state.period, 
                                start_date=st.session_state.start_date, 
                                end_date=st.session_state.end_date
                            )
                        else:
                            st.session_state.data = load_yfinance_data(
                                st.session_state.symbol, 
                                st.session_state.period
                            )
                        if st.session_state.data.empty:
                            st.error(
                                f"No data found for {st.session_state.symbol} in period {st.session_state.period}. "
                                f"Try 1M, Custom (post-2021 for CING), another symbol (e.g., AAPL), or File Import."
                            )
                        else:
                            st.success(f"Data loaded for {st.session_state.symbol}")
                    except Exception as e:
                        st.error(f"Error loading data: {str(e)}")
    
    with col6:
        if st.button("Clear", key="clear"):
            st.session_state.data = None
            st.session_state.symbol = "AAPL"
            st.session_state.period = "1Y"
            st.session_state.start_date = None
            st.session_state.end_date = None
            st.session_state.is_custom_symbol = False
            st.experimental_rerun()

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
        st.experimental_rerun()

# Display Data and Analysis
if st.session_state.data is not None and not st.session_state.data.empty:
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    
    with st.expander("View Raw Data"):
        st.dataframe(st.session_state.data)
    
    if data_source == "Yahoo Finance":
        try:
            import yfinance as yf
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
