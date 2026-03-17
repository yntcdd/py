import pandas as pd
import yfinance as yf
import time

# Load your portfolio CSV
portfolio_df = pd.read_csv("my_portfolio.csv")

tickers_list = portfolio_df["Ticker"].tolist()

# Fetch latest prices and add directly to the same DataFrame
start = time.perf_counter()
tkrs = yf.Tickers(" ".join(tickers_list))

latest_prices = []
for symbol, tkr in tkrs.tickers.items():
    try:
        hist = tkr.history(period="1d")
        if hist.empty:
            latest_prices.append(None)
        else:
            latest_prices.append(hist["Close"].iloc[-1])
    except Exception:
        latest_prices.append(None)

# Assign Latest Price column
portfolio_df["Latest Price"] = latest_prices

end = time.perf_counter()
print(f"Fetch completed in {end - start:.2f} seconds\n")

# Calculate Difference and Earnings
portfolio_df["Difference"] = portfolio_df["Latest Price"] - portfolio_df["Purchase Price"]
portfolio_df["Earnings"] = portfolio_df["Difference"] * portfolio_df["Number of Shares"]

# Sort by earnings descending
portfolio_df = portfolio_df.sort_values(by="Earnings", ascending=False).reset_index(drop=True)

# Display the portfolio
print("Portfolio Performance (sorted by earnings):")
print(portfolio_df.to_string(formatters={
    "Purchase Price": "{:,.2f}".format,
    "Latest Price": "{:,.2f}".format,
    "Difference": "{:,.2f}".format,
    "Earnings": "{:,.2f}".format
}))

# Total earnings
total_earnings = portfolio_df["Earnings"].sum()
print(f"\nTotal Earnings: ${total_earnings:,.2f}")
