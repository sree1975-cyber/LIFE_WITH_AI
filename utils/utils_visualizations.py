import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def create_monthly_pl_table(pl_data, period):
    """Create a monthly P/L table/chart with years as rows and months as columns."""
    pl_data['Year'] = pl_data.index.year
    pl_data['Month'] = pl_data.index.month_name()
    monthly_pl = pl_data.groupby(['Year', 'Month'])['% P/L'].mean().unstack().fillna(0)
    fig = px.imshow(monthly_pl, 
                    labels=dict(x="Month", y="Year", color="% P/L"),
                    x=monthly_pl.columns,
                    y=monthly_pl.index,
                    color_continuous_scale='RdYlGn')
    fig.update_layout(title="Monthly % P/L Comparison")
    return fig

def create_candlestick_chart(pl_data):
    """Create an interactive candlestick chart with volume and indicators."""
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=pl_data.index,
        open=pl_data['open'],
        high=pl_data['high'],
        low=pl_data['low'],
        close=pl_data['close'],
        name="Price"
    ))
    
    # Volume
    fig.add_trace(go.Bar(
        x=pl_data.index,
        y=pl_data['volume'],
        name="Volume",
        yaxis="y2",
        opacity=0.3
    ))
    
    # SMA
    if 'SMA_20' in pl_data.columns:
        fig.add_trace(go.Scatter(
            x=pl_data.index,
            y=pl_data['SMA_20'],
            name="SMA (20-day)",
            line=dict(color='blue')
        ))
    
    # RSI (on secondary axis)
    if 'RSI_14' in pl_data.columns:
        fig.add_trace(go.Scatter(
            x=pl_data.index,
            y=pl_data['RSI_14'],
            name="RSI (14-day)",
            yaxis="y3",
            line=dict(color='purple')
        ))
    
    # MACD
    if 'MACD' in pl_data.columns:
        fig.add_trace(go.Scatter(
            x=pl_data.index,
            y=pl_data['MACD'],
            name="MACD",
            yaxis="y4",
            line=dict(color='green')
        ))
        fig.add_trace(go.Scatter(
            x=pl_data.index,
            y=pl_data['MACD_Signal'],
            name="MACD Signal",
            yaxis="y4",
            line=dict(color='red')
        ))
    
    # Anomaly Markers
    anomalies = pl_data[pl_data['Anomaly Flag']]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies.index,
            y=anomalies['close'],
            mode='markers',
            name="Anomalies",
            marker=dict(color='red', size=10, symbol='x')
        ))
    
    # Layout
    fig.update_layout(
        title="Candlestick Chart with Indicators",
        yaxis=dict(title="Price"),
        yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False),
        yaxis3=dict(title="RSI", overlaying="y", side="right", position=0.85, showgrid=False),
        yaxis4=dict(title="MACD", overlaying="y", side="right", position=0.95, showgrid=False),
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )
    return fig