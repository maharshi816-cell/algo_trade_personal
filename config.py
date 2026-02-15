import json

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

capital = config["trading_capital"]
risk_per_trade = config["max_risk_per_trade"]
daily_loss_limit = config["max_daily_loss"]
stop_loss = config["stop_loss"]
target = config["target"]
paper_trading = config["paper_trading"]

print("Config loaded:")
print(config)
