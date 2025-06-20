import streamlit as st
import pandas as pd
import re
from utils.yfetch import fetch_yfinance_data

# Set page configuration
st.set_page_config(page_title="Stock Data Fetcher", layout="wide")

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

# Main UI
st.title("Stock Data Fetcher")

st.header("Yahoo Finance Data")
col1, col2 = st.columns([2, 1])

with col1:
    symbols = ["AAPL", "TSLA", "CING"]
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
        st.info("CING data is available from December 2021. Use periods like 1M, 5D, or Custom (post-2021).")

with col2:
    periods = ["1D", "5D", "1M", "YTD", "1Y", "MAX", "Custom"]
    st.session_state.period = st.selectbox("Select Period", periods, 
                                           index=periods.index(st.session_state.period) if st.session_state.period in periods else 0,
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
                        st.session_state.data = fetch_yfinance_data(
                            st.session_state.symbol, 
                            start_date=st.session_state.start_date, 
                            end_date=st.session_state.end_date
                        )
                    else:
                        st.session_state.data = fetch_yfinance_data(
                            st.session_state.symbol, 
                            period=st.session_state.period
                        )
                    if st.session_state.data.empty:
                        suggestions = ["1M", "5D", "Custom (post-2021)" if st.session_state.symbol == "CING" else "Custom"]
                        st.error(
                            f"No data found for {st.session_state.symbol} in period {st.session_state.period if st.session_state.period else f'{st.session_state.start_date} to {st.session_state.end_date}'}. "
                            f"Try:\n"
                            f"- Different periods like: {', '.join(suggestions)}\n"
                            f"- Another symbol (e.g., MSFT, GOOGL)"
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

# Display Data
if st.session_state.data is not None and not st.session_state.data.empty:
    st.session_state.data.columns = st.session_state.data.columns.str.lower()
    st.write("Fetched Data")
    st.dataframe(st.session_state.data)
    st.info(f"Data from {st.session_state.data.index[0].date()} to {st.session_state.data.index[-1].date()}")
