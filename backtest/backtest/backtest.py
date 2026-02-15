import pandas as pd

# --- Parameters ---
EMA_PERIOD = 20
TARGET = 0.02   # 2% profit target
STOP_LOSS = 0.01  # 1% stop loss

# --- Load Data ---
df = pd.read_csv("data.csv")  # CSV must have columns: Date, Open, High, Low, Close, Volume
df['EMA'] = df['Close'].ewm(span=EMA_PERIOD, adjust=False).mean()

# VWAP calculation
df['CumVol'] = df['Volume'].cumsum()
df['CumPV'] = (df['Close'] * df['Volume']).cumsum()
df['VWAP'] = df['CumPV'] / df['CumVol']

# --- Backtest ---
position = None
entry_price = 0
pnl = 0

for i in range(len(df)):
    close = df['Close'].iloc[i]
    ema = df['EMA'].iloc[i]
    vwap = df['VWAP'].iloc[i]

    if position is None:
        # Entry condition: BUY when close > EMA and close > VWAP
        if close > ema and close > vwap:
            position = "LONG"
            entry_price = close
            print(f"BUY at {entry_price} on {df['Date'].iloc[i]}")
    else:
        # Exit conditions
        if close >= entry_price * (1 + TARGET):
            pnl += (close - entry_price)
            print(f"TARGET HIT: Exit at {close} | PnL: {close - entry_price}")
            position = None
        elif close <= entry_price * (1 - STOP_LOSS):
            pnl += (close - entry_price)
            print(f"STOP LOSS: Exit at {close} | PnL: {close - entry_price}")
            position = None

print(f"\nTotal PnL: {pnl}")
