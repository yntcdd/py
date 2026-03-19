import pandas as pd
import yfinance as yf
import time

# Load portfolio CSV
portfolio_df = pd.read_csv("my_portfolio.csv")

# Fetch latest prices using yf.Tickers
tickers_list = portfolio_df["Ticker"].tolist()
start = time.perf_counter()
tkrs = yf.Tickers(" ".join(tickers_list))

latest_prices = []
for symbol, tkr in tkrs.tickers.items():
    try:
        hist = tkr.history(period="1d")
        if hist.empty:
            continue
        latest_price = hist["Close"].iloc[-1]
        latest_prices.append(latest_price)
    except Exception:
        latest_prices.append(None)  # Keep None if failed

end = time.perf_counter()
print(f"Fetch completed in {end - start:.2f} seconds\n")

# Add Latest Price column directly
portfolio_df["Latest Price"] = latest_prices

# Calculate Difference and Earnings
portfolio_df["Difference"] = portfolio_df["Latest Price"] - portfolio_df["Purchase Price"]
portfolio_df["Earnings"] = portfolio_df["Difference"] * portfolio_df["Number of Shares"]

# Sort by Earnings descending
portfolio_df = portfolio_df.sort_values(by="Earnings", ascending=False).reset_index(drop=True)

# Display table
print("Portfolio Performance (sorted by earnings):")
print(portfolio_df.to_string(formatters={
    "Purchase Price": "{:,.2f}".format,
    "Latest Price": "{:,.2f}".format,
    "Difference": "{:,.2f}".format,
    "Earnings": "{:,.2f}".format
}))

# Calculate total earnings
total_earnings = portfolio_df["Earnings"].sum()
print(f"\nTotal Earnings: ${total_earnings:,.2f}")