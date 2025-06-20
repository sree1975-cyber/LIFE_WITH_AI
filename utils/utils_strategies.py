import pandas as pd

def apply_strategies(data):
    """Apply trading strategies: Mean Reversion and Momentum."""
    df = data.copy()
    
    # Mean Reversion: Buy when price < SMA_20 by 5%, Sell when > SMA_20 by 5%
    df['Mean_Reversion_Signal'] = 'Hold'
    df.loc[df['close'] < df['SMA_20'] * 0.95, 'Mean_Reversion_Signal'] = 'Buy'
    df.loc[df['close'] > df['SMA_20'] * 1.05, 'Mean_Reversion_Signal'] = 'Sell'
    
    # Momentum: Buy when RSI < 30, Sell when RSI > 70
    df['Momentum_Signal'] = 'Hold'
    df.loc[df['RSI_14'] < 30, 'Momentum_Signal'] = 'Buy'
    df.loc[df['RSI_14'] > 70, 'Momentum_Signal'] = 'Sell'
    
    return df