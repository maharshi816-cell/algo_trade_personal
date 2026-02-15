import pandas as pd

def calculate_ema(data, period):
    """
    Calculate Exponential Moving Average (EMA).
    
    Parameters:
    -----------
    data : pd.Series
        Price series
    period : int
        EMA period
    
    Returns:
    --------
    pd.Series
        EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_vwap(df):
    """
    Calculate Volume Weighted Average Price (VWAP).
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'high', 'low', 'close', and 'volume' columns
    
    Returns:
    --------
    pd.Series
        VWAP values
    """
    df = df.copy()
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    return df['vwap']


def calculate_rsi(data, period=14):
    """
    Calculate Relative Strength Index (RSI).
    
    Parameters:
    -----------
    data : pd.Series
        Price series
    period : int
        RSI period (default: 14)
    
    Returns:
    --------
    pd.Series
        RSI values
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def trading_strategy(df):
    """
    Trading strategy that generates BUY or NO_TRADE signals.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with OHLCV data (must contain 'open', 'high', 'low', 'close', 'volume' columns)
    
    Returns:
    --------
    str
        'BUY' if all conditions are met, 'NO_TRADE' otherwise
    
    Conditions for BUY signal:
    - EMA 20 > EMA 50
    - Close price > VWAP
    - RSI is between 50 and 65
    """
    df = df.copy()
    
    # Calculate indicators
    df['ema_20'] = calculate_ema(df['close'], 20)
    df['ema_50'] = calculate_ema(df['close'], 50)
    df['vwap'] = calculate_vwap(df)
    df['rsi'] = calculate_rsi(df['close'], period=14)
    
    # Get the latest values
    latest_idx = len(df) - 1
    ema_20 = df['ema_20'].iloc[latest_idx]
    ema_50 = df['ema_50'].iloc[latest_idx]
    close = df['close'].iloc[latest_idx]
    vwap = df['vwap'].iloc[latest_idx]
    rsi = df['rsi'].iloc[latest_idx]
    
    # Check all conditions
    condition_1 = ema_20 > ema_50
    condition_2 = close > vwap
    condition_3 = 50 <= rsi <= 65
    
    # Return signal
    if condition_1 and condition_2 and condition_3:
        return "BUY"
    else:
        return "NO_TRADE"
      Add EMA + VWAP strategy
