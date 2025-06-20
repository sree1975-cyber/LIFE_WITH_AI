import streamlit as st
import pandas as pd
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
    st.session_state.symbol = ""
if 'period' not in st.session_state:
    st.session_state.period = "1Y"
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None

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
        st.session_state.symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)", value=st.session_state.symbol)
    with col2:
        periods = ["1D", "5D", "15D", "30D", "1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "5Y", "MAX", "Custom"]
        st.session_state.period = st.selectbox("Select Period", periods, index=periods.index(st.session_state.period))
    
    if st.session_state.period == "Custom":
        col3, col4 = st.columns(2)
        with col3:
            st.session_state.start_date = st.date_input("Start Date", value=pd.to_datetime("today") - pd.Timedelta(days=365))
        with col4:
            st.session_state.end_date = st.date_input("End Date", value=pd.to_datetime("today"))
    
    col5, col6 = st.columns(2)
    with col5:
        if st.button("Submit"):
            if st.session_state.symbol:
                try:
                    if st.session_state.period == "Custom":
                        st.session_state.data = load_yfinance_data(
                            st.session_state.symbol, 
                            st.session_state.period, 
                            start_date=st.session_state.start_date, 
                            end_date=st.session_state.end_date
                        )
                    else:
                        st.session_state.data = load_yfinance_data(st.session_state.symbol, st.session_state.period)
                    st.success(f"Data loaded for {st.session_state.symbol}")
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
    with col6:
        if st.button("Clear"):
            st.session_state.data = None
            st.session_state.symbol = ""
            st.session_state.period = "1Y"
            st.session_state.start_date = None
            st.session_state.end_date = None
            st.experimental_rerun()

# File Import UI
else:
    st.header("File Import")
    uploaded_file = st.file_uploader("Upload .csv or .xlsx file", type=["csv", "xlsx"])
    if st.button("Process"):
        if uploaded_file:
            try:
                st.session_state.data = load_file_data(uploaded_file)
                st.success("File data loaded successfully")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    if st.button("Clear"):
        st.session_state.data = None
        st.experimental_rerun()

# Display Data and Analysis
if st.session_state.data is not None:
    # Normalize column names
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    
    # Display Raw Data
    with st.expander("View Raw Data"):
        st.dataframe(st.session_state.data)
    
    # Yahoo Finance Messages
    if data_source == "Yahoo Finance" and st.session_state.data is not None:
        try:
            import yfinance as yf
            ticker = yf.Ticker(st.session_state.symbol)
            hist_data = ticker.history(period="max")
            if not hist_data.empty:
                st.info(f"Total historical data available from {hist_data.index[0].date()} to {hist_data.index[-1].date()}")
            st.info(f"Selected period data from {st.session_state.data.index[0].date()} to {st.session_state.data.index[-1].date()}")
        except:
            st.warning("Unable to fetch historical data range.")

    # Calculate P/L and Indicators
    pl_data = calculate_pl(st.session_state.data)
    pl_data = calculate_indicators(pl_data)
    pl_data = apply_strategies(pl_data)
    
    # Display P/L Table
    with st.expander("Profit and Loss Analysis"):
        st.dataframe(pl_data)
    
    # Monthly P/L Table
    monthly_pl = create_monthly_pl_table(pl_data, st.session_state.period)
    with st.expander("Monthly P/L Comparison"):
        st.plotly_chart(monthly_pl, use_container_width=True)
    
    # Candlestick Chart
    candlestick_chart = create_candlestick_chart(pl_data)
    with st.expander("Candlestick Chart"):
        st.plotly_chart(candlestick_chart, use_container_width=True)
    
    # Price Prediction
    with st.expander("Price Prediction"):
        horizon = st.selectbox("Prediction Horizon", ["1 Day", "5 Days", "1 Month"])
        horizon_map = {"1 Day": 1, "5 Days": 5, "1 Month": 30}
        try:
            pred_df, pred_chart = predict_prices(pl_data, horizon_map[horizon])
            st.dataframe(pred_df)
            st.plotly_chart(pred_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Error in prediction: {str(e)}")

# Export Data
if st.session_state.data is not None:
    st.header("Export Data")
    export_format = st.selectbox("Select Export Format", ["CSV", "XLSX"])
    export_data = pl_data if st.session_state.data is not None else st.session_state.data
    if export_format == "CSV":
        csv = export_data.to_csv(index=True)
        st.download_button("Download Data", csv, f"stock_data_{st.session_state.symbol or 'file'}.csv", "text/csv")
    else:
        import io
        output = io.BytesIO()
        export_data.to_excel(output, index=True)
        output.seek(0)
        st.download_button("Download Data", output, f"stock_data_{st.session_state.symbol or 'file'}.xlsx", 
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")