import pandas as pd
import numpy as np

def calculate_pl(data):
    """Calculate daily profit/loss and anomaly flag."""
    pl_data = data.copy()
    pl_data['P/L Value'] = pl_data['close'] - pl_data['open']
    pl_data['% P/L'] = (pl_data['P/L Value'] / pl_data['open'] * 100).round(2)
    
    # Z-score for anomaly detection
    pl_data['Z-Score P/L'] = (pl_data['% P/L'] - pl_data['% P/L'].mean()) / pl_data['% P/L'].std()
    pl_data['Z-Score Volume'] = (pl_data['volume'] - pl_data['volume'].mean()) / pl_data['volume'].std()
    pl_data['Anomaly Flag'] = (pl_data['Z-Score P/L'].abs() > 2) | (pl_data['Z-Score Volume'].abs() > 2)
    
    return pl_data[['open', 'high', 'low', 'close', 'P/L Value', '% P/L', 'volume', 'Z-Score P/L', 'Z-Score Volume', 'Anomaly Flag']]
