import pandas as pd
import json

# --- Risk Manager Class ---
class RiskManager:
    def __init__(self, config):
        self.capital = config["trading_capital"]
        self.max_risk_per_trade = config["max_risk_per_trade"]
        self.max_daily_loss = config["max_daily_loss"]
        self.stop_loss = config["stop_loss"]
        self.target = config["target"]
        self.paper_trading = config["paper_trading"]

        self.daily_pnl = 0
        self.total_pnl = 0
        self.open_position = None
        self.entry_price = None
        self.current_day = None

        # Trade log storage
        self.trade_log = []

    def reset_day(self, day):
        if self.current_day is not None:
            print(f"--- End of {self.current_day} | Daily PnL: {self.daily_pnl:.2f} ---\n")
            self.total_pnl += self.daily_pnl
        self.daily_pnl = 0
        self.open_position = None
        self.entry_price = None
        self.current_day = day
        print(f"\n=== New Trading Day: {day} ===")

    def can_trade(self):
        return self.daily_pnl > -self.capital * self.max_daily_loss

    def enter_trade(self, price, date):
        risk_amount = self.capital * self.max_risk_per_trade
        self.open_position = "LONG"
        self.entry_price = price
        print(f"[{date}] ENTER LONG at {price:.2f} | Risk: {risk_amount:.2f}")

    def exit_trade(self, price, date, reason):
        if self.open_position == "LONG":
            trade_pnl = price - self.entry_price
            self.daily_pnl += trade_pnl
            print(f"[{date}] EXIT LONG at {price:.2f} | {reason} | Trade PnL: {trade_pnl:.2f}")

            # Save trade details to log
            self.trade_log.append({
                "Date": date,
                "EntryPrice": self.entry_price,
                "ExitPrice": price,
                "Reason": reason,
                "TradePnL": trade_pnl,
                "Day": self.current_day
            })

        self.open_position = None
        self.entry_price = None

    def final_summary(self):
        if self.current_day is not None:
            print(f"--- End of {self.current_day} | Daily PnL: {self.daily_pnl:.2f} ---")
            self.total_pnl += self.daily_pnl
        print(f"\n=== Backtest Complete ===")
        print(f"Total Cumulative PnL: {self.total_pnl:.2f}")

        # Export trade log to CSV
        if self.trade_log:
            df_log = pd.DataFrame(self.trade_log)
            df_log.to_csv("trade_log.csv", index=False)
            print("Trade log exported to trade_log.csv")


# --- Load Config ---
with open("config.json", "r") as f:
    config = json.load(f)

rm = RiskManager(config)

# --- Load Data ---
df = pd.read_csv("data.csv")  # must have Date, Open, High, Low, Close, Volume
df['Date'] = pd.to_datetime(df['Date'])
df['EMA'] = df['Close'].ewm(span=20, adjust=False).mean()
df['CumVol'] = df['Volume'].cumsum()
df['CumPV'] = (df['Close'] * df['Volume']).cumsum()
df['VWAP'] = df['CumPV'] / df['CumVol']

# --- Main Loop ---
for i in range(len(df)):
    date = df['Date'].iloc[i]
    day = date.date()
    close = df['Close'].iloc[i]
    ema = df['EMA'].iloc[i]
    vwap = df['VWAP'].iloc[i]

    # Reset daily stats if new day
    if rm.current_day != day:
        rm.reset_day(day)

    # Generate signal
    signal = None
    if close > ema and close > vwap:
        signal = "BUY"

    print(f"[{date}] Signal: {signal if signal else 'NONE'} | Close={close:.2f}, EMA={ema:.2f}, VWAP={vwap:.2f}")

    # Trading logic
    if rm.open_position is None and signal == "BUY":
        if rm.can_trade():
            rm.enter_trade(close, date)
        else:
            print(f"[{date}] Trade blocked: Daily loss limit reached")

    elif rm.open_position == "LONG":
        # Exit conditions
        if close >= rm.entry_price * (1 + rm.target):
            rm.exit_trade(close, date, "TARGET HIT")
        elif close <= rm.entry_price * (1 - rm.stop_loss):
            rm.exit_trade(close, date, "STOP LOSS")

# --- Final Summary ---
rm.final_summary()
