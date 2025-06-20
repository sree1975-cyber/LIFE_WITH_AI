import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import os

# Import utility modules
from utils.data_loader import DataLoader
from utils.data_processor import DataProcessor
from utils.ml_models.minimal_models import MinimalModelManager as ModelManager
from utils.visualizations import create_comparison_chart, create_pl_table, create_anomaly_chart
from utils.config_manager import ConfigManager
from utils.performance_metrics import PerformanceMetrics

# Page configuration
st.set_page_config(
    page_title="Advanced Financial Analysis Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = "YFinance"
if 'symbol' not in st.session_state:
    st.session_state.symbol = ""
if 'period' not in st.session_state:
    st.session_state.period = "1y"

# Initialize utility classes
data_loader = DataLoader()
data_processor = DataProcessor()
model_manager = ModelManager()
config_manager = ConfigManager()
performance_metrics = PerformanceMetrics()

def main():
    st.title("📈 Advanced Financial Analysis Platform")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select Page",
            ["Data Input & Analysis", "ML Model Configuration", "Performance Dashboard"]
        )
    
    if page == "Data Input & Analysis":
        data_input_page()
    elif page == "ML Model Configuration":
        model_config_page()
    else:
        performance_dashboard_page()

def data_input_page():
    # Data source selection
    st.header("📊 Data Input & Analysis")
    
    data_source = st.radio(
        "Select Data Source",
        ["YFinance", "File Upload"],
        key="data_source_radio"
    )
    
    st.session_state.data_source = data_source
    
    col1, col2 = st.columns([2, 1])
    
    if data_source == "YFinance":
        with col1:
            display_yfinance_interface()
    else:
        with col1:
            display_file_upload_interface()
    
    with col2:
        if st.button("🔄 Clear All Data", type="secondary"):
            clear_data()
            st.rerun()
    
    # Display data analysis if data is available
    if st.session_state.data is not None:
        display_data_analysis()

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
            with st.spinner("Downloading data from YFinance..."):
                try:
                    data = data_loader.load_yfinance_data(symbol, period, start_date, end_date)
                    if data is not None and not data.empty:
                        st.session_state.data = data
                        st.session_state.symbol = symbol
                        st.session_state.period = period if period else f"{start_date} to {end_date}"
                        
                        # Process data
                        st.session_state.processed_data = data_processor.process_stock_data(data)
                        
                        st.success(f"✅ Data downloaded successfully for {symbol}")
                        
                        # Display data info
                        display_data_info(data, symbol)
                        st.rerun()
                    else:
                        st.error("❌ No data found for the specified symbol and period")
                except Exception as e:
                    st.error(f"❌ Error downloading data: {str(e)}")
        else:
            st.warning("⚠️ Please enter a stock symbol")

def display_file_upload_interface():
    st.subheader("File Upload")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls']
    )
    
    if uploaded_file is not None:
        if st.button("📤 Process File", type="primary"):
            with st.spinner("Processing uploaded file..."):
                try:
                    data = data_loader.load_file_data(uploaded_file)
                    if data is not None and not data.empty:
                        st.session_state.data = data
                        st.session_state.processed_data = data_processor.process_stock_data(data)
                        st.success("✅ File processed successfully")
                        
                        # Display data info
                        display_data_info(data, "Uploaded File")
                        st.rerun()
                    else:
                        st.error("❌ Unable to process the uploaded file")
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")

def display_data_info(data, source):
    """Display information about the loaded data"""
    st.info(f"""
    📋 **Data Information for {source}:**
    - Total Records: {len(data):,}
    - Date Range: {data.index.min().strftime('%Y-%m-%d')} to {data.index.max().strftime('%Y-%m-%d')}
    - Columns: {', '.join(data.columns.tolist())}
    """)

def display_data_analysis():
    """Display comprehensive data analysis"""
    st.header("📊 Data Analysis & Insights")
    
    if st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        
        # Create tabs for different analyses
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Raw Data", 
            "💰 P&L Analysis", 
            "🔮 ML Predictions", 
            "📅 Year Comparison", 
            "🚨 Anomaly Detection"
        ])
        
        with tab1:
            display_raw_data_tab(data)
        
        with tab2:
            display_pl_analysis_tab(data)
        
        with tab3:
            display_ml_predictions_tab(data)
        
        with tab4:
            display_year_comparison_tab(data)
        
        with tab5:
            display_anomaly_detection_tab(data)

def display_raw_data_tab(data):
    """Display raw data with expandable sections"""
    st.subheader("📈 Stock Data Overview")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${data['Close'].iloc[-1]:.2f}")
    with col2:
        change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
        st.metric("Daily Change", f"${change:.2f}", f"{(change/data['Close'].iloc[-2]*100):.2f}%")
    with col3:
        st.metric("52W High", f"${data['High'].max():.2f}")
    with col4:
        st.metric("52W Low", f"${data['Low'].min():.2f}")
    
    # Interactive chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Price"
    ))
    
    fig.update_layout(
        title="Stock Price Chart",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Expandable data view
    with st.expander("📋 View Raw Data"):
        st.dataframe(data.tail(100), use_container_width=True)

def display_pl_analysis_tab(data):
    """Display profit and loss analysis"""
    st.subheader("💰 Profit & Loss Analysis")
    
    # Calculate P&L
    pl_data = data_processor.calculate_pl(data)
    
    # P&L Summary
    col1, col2, col3, col4 = st.columns(4)
    
    total_pl = pl_data['PL_Value'].sum()
    positive_days = len(pl_data[pl_data['PL_Value'] > 0])
    negative_days = len(pl_data[pl_data['PL_Value'] < 0])
    win_rate = positive_days / len(pl_data) * 100
    
    with col1:
        st.metric("Total P&L", f"${total_pl:.2f}")
    with col2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Positive Days", positive_days)
    with col4:
        st.metric("Negative Days", negative_days)
    
    # P&L Chart
    fig = create_pl_table(pl_data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed P&L table with expandable view
    with st.expander("📊 Detailed P&L Table"):
        st.dataframe(pl_data, use_container_width=True)

def display_ml_predictions_tab(data):
    """Display ML predictions and model results"""
    st.subheader("🔮 Machine Learning Predictions")
    
    # Model selection
    model_categories = model_manager.get_available_models()
    
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox("Select Model Category", list(model_categories.keys()))
    with col2:
        selected_model = st.selectbox("Select Model", model_categories[selected_category])
    
    if st.button("🚀 Train & Predict", type="primary"):
        with st.spinner(f"Training {selected_model} model..."):
            try:
                # Train model and make predictions
                model_results = model_manager.train_and_predict(
                    data, selected_category, selected_model
                )
                
                if model_results:
                    st.success("✅ Model trained successfully!")
                    
                    # Display predictions
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Predicted Next Price", f"${model_results['next_price']:.2f}")
                        st.metric("Prediction Confidence", f"{model_results['confidence']:.1f}%")
                    
                    with col2:
                        st.metric("Model Accuracy", f"{model_results['accuracy']:.2f}%")
                        st.metric("RMSE", f"{model_results['rmse']:.4f}")
                    
                    # Prediction chart
                    if 'predictions' in model_results:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=data.index[-len(model_results['predictions']):],
                            y=data['Close'].iloc[-len(model_results['predictions']):],
                            mode='lines',
                            name='Actual',
                            line=dict(color='blue')
                        ))
                        fig.add_trace(go.Scatter(
                            x=data.index[-len(model_results['predictions']):],
                            y=model_results['predictions'],
                            mode='lines',
                            name='Predicted',
                            line=dict(color='red', dash='dash')
                        ))
                        
                        fig.update_layout(
                            title=f"{selected_model} Predictions vs Actual",
                            xaxis_title="Date",
                            yaxis_title="Price ($)",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error training model: {str(e)}")

def display_year_comparison_tab(data):
    """Display year-over-year comparison"""
    st.subheader("📅 Year-over-Year Comparison")
    
    # Create year-over-year comparison
    comparison_data = data_processor.create_year_comparison(data)
    
    if comparison_data is not None:
        # Create heatmap
        fig = create_comparison_chart(comparison_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Year summary table
        with st.expander("📊 Year Summary Statistics"):
            yearly_stats = data_processor.calculate_yearly_stats(data)
            st.dataframe(yearly_stats, use_container_width=True)
    else:
        st.info("ℹ️ Insufficient data for year-over-year comparison. Need at least 2 years of data.")

def display_anomaly_detection_tab(data):
    """Display anomaly detection results"""
    st.subheader("🚨 Anomaly Detection")
    
    # Anomaly detection controls
    col1, col2 = st.columns(2)
    
    with col1:
        anomaly_method = st.selectbox(
            "Detection Method",
            ["Isolation Forest", "Statistical", "DBSCAN", "One-Class SVM"]
        )
    
    with col2:
        sensitivity = st.slider("Sensitivity", 0.01, 0.5, 0.1, 0.01)
    
    if st.button("🔍 Detect Anomalies", type="primary"):
        with st.spinner("Detecting anomalies..."):
            try:
                anomalies = data_processor.detect_anomalies(data, anomaly_method, sensitivity)
                
                if anomalies is not None:
                    anomaly_count = len(anomalies[anomalies['Anomaly'] == True])
                    st.metric("Anomalies Detected", anomaly_count)
                    
                    # Anomaly chart
                    fig = create_anomaly_chart(data, anomalies)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Anomalies table
                    if anomaly_count > 0:
                        with st.expander("🚨 Anomaly Details"):
                            anomaly_details = anomalies[anomalies['Anomaly'] == True]
                            st.dataframe(anomaly_details, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error detecting anomalies: {str(e)}")

def model_config_page():
    """ML Model Configuration Page"""
    st.header("⚙️ ML Model Configuration")
    
    # Model categories
    categories = model_manager.get_available_models()
    
    for category, models in categories.items():
        with st.expander(f"🔧 {category} Models"):
            st.write(f"Available models: {', '.join(models)}")
            
            # Configuration for each model
            for model in models:
                st.subheader(f"{model} Configuration")
                config = config_manager.get_model_config(category, model)
                
                # Display current configuration
                if config:
                    st.json(config)
                else:
                    st.info("Using default configuration")
                
                # Allow parameter modification
                if st.button(f"Configure {model}", key=f"config_{model}"):
                    st.write("Configuration interface would be implemented here")

def performance_dashboard_page():
    """Performance Dashboard Page"""
    st.header("📊 Performance Dashboard")
    
    if st.session_state.processed_data is not None:
        data = st.session_state.processed_data
        
        # Performance metrics
        metrics = performance_metrics.calculate_all_metrics(data)
        
        # Display metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.3f}")
        with col2:
            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2%}")
        with col3:
            st.metric("Volatility", f"{metrics.get('volatility', 0):.2%}")
        with col4:
            st.metric("Total Return", f"{metrics.get('total_return', 0):.2%}")
        
        # Performance charts
        fig = performance_metrics.create_performance_chart(data)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("ℹ️ Please load data first to view performance metrics")

def clear_data():
    """Clear all session state data"""
    st.session_state.data = None
    st.session_state.processed_data = None
    st.session_state.symbol = ""
    st.session_state.period = "1y"

if __name__ == "__main__":
    main()
