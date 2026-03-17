import pandas as pd
import yfinance as yf
import time
import threading

# Load your portfolio CSV
portfolio_df = pd.read_csv("my_portfolio.csv")

tickers_list = portfolio_df["Ticker"].tolist()

# Fetch latest prices and add directly to the same DataFrame

latest_prices = []

def fetch_latest_price(tickers):
    start = time.perf_counter()
    tkrs = yf.Tickers(" ".join(tickers))

    for symbol, tkr in tkrs.tickers.items():
        try:
            hist = tkr.history(period="1d")
            if hist.empty:
                latest_prices.append(None)
            else:
                latest_prices.append(hist["Close"].iloc[-1])
        except Exception:
            latest_prices.append(None)

    end = time.perf_counter()
    print(f"Fetch completed in {end - start:.2f} seconds\n")

def display_dataframe(df):
    # Assign Latest Price column
    df["Latest Price"] = latest_prices

    # Calculate Difference and Earnings
    df["Difference"] = df["Latest Price"] - df["Purchase Price"]
    df["P/L(%)"] = df["Difference"] / df["Purchase Price"] * 100
    df["P/L"] = df["Difference"] * df["Number of Shares"]

    # Sort by P/L descending
    df = df.sort_values(by="P/L", ascending=False).reset_index(drop=True)

    # Display the portfolio
    print("Portfolio Performance:\n")
    print(df.to_string(formatters={
        "Purchase Price": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}",
        "Latest Price": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}",
        "Difference": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}",
        "P/L(%)": lambda x: f"{x:,.2f}%",
        "P/L": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}"
    }))

    # Total Costs
    total_costs = (df["Purchase Price"] * df["Number of Shares"]).sum()
    print(f"\nTotal Investment: ${total_costs:,.2f}")

    # Total current value
    total_current_value = (df["Latest Price"] * df["Number of Shares"]).sum()
    print(f"Total Current Value: ${total_current_value:,.2f}")

    # Total percentage change
    total_percentage_change = (total_current_value - total_costs) / total_costs * 100
    print(f"Total Percentage Change: {total_percentage_change:,.2f}%")

    # Total earnings
    total_earnings = df["P/L"].sum() 
    if total_earnings >= 0:
        print(f"Total Profit: ${total_earnings:,.2f}")
    else:
        print(f"Total Loss: -${abs(total_earnings):,.2f}")

# while True:
#     fetch_latest_price(tickers_list)
#     display_dataframe(portfolio_df)
#     time.sleep(60)  # Update every 60 seconds