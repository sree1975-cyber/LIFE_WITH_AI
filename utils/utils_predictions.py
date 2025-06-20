import pandas as pd
from prophet import Prophet
import plotly.express as px

def predict_prices(data, horizon):
    """Predict future prices using Prophet."""
    df = data[['close']].reset_index().rename(columns={'Date': 'ds', 'close': 'y'})
    
    # Train Prophet model
    model = Prophet(daily_seasonality=True)
    model.fit(df)
    
    # Create future dataframe
    future = model.make_future_dataframe(periods=horizon)
    forecast = model.predict(future)
    
    # Filter predictions for future dates
    pred_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizon)
    pred_df.columns = ['Date', 'Predicted Close', 'Lower Bound', 'Upper Bound']
    
    # Create prediction chart
    fig = px.line(pred_df, x='Date', y='Predicted Close', title=f"Price Prediction ({horizon} Days)")
    fig.add_scatter(x=pred_df['Date'], y=pred_df['Lower Bound'], mode='lines', name='Lower Bound', line=dict(dash='dash'))
    fig.add_scatter(x=pred_df['Date'], y=pred_df['Upper Bound'], mode='lines', name='Upper Bound', line=dict(dash='dash'))
    
    return pred_df, fig