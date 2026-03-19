import pandas as pd
import yfinance as yf
import time
import threading
import sys
from datetime import datetime

# Load your portfolio CSV
portfolio_df = pd.read_csv("my_portfolio.csv")
tickers_list = portfolio_df["Ticker"].tolist()

# Shared latest prices list
latest_prices = [None] * len(tickers_list)
lock = threading.Lock()
fetch_complete = threading.Event()

def fetch_latest_price():
    global latest_prices
    while True:
        tkrs = yf.Tickers(" ".join(tickers_list))
        temp_prices = []

        for symbol, tkr in tkrs.tickers.items():
            try:
                hist = tkr.history(period="1d")
                temp_prices.append(hist["Close"].iloc[-1] if not hist.empty else 0)
            except Exception:
                temp_prices.append(0)

        with lock:
            latest_prices = temp_prices.copy()
            fetch_complete.set()  # data is ready

        time.sleep(30)  # Fetch every 30 seconds

# Start fetch thread
threading.Thread(target=fetch_latest_price, daemon=True).start()

# Initialize display DataFrame
df_display = portfolio_df.copy()
df_display["Latest Price"] = [None] * len(df_display)

try:
    while True:
        sys.stdout.write("\033[H\033[K")
        now = datetime.now()
        print(f"Portfolio Performance - {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Update table
        if fetch_complete.is_set():
            with lock:
                df_display["Latest Price"] = latest_prices.copy()
            # Calculate Difference, P/L%, P/L
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            print(f"Portfolio Performance - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            df_display["Difference"] = df_display["Latest Price"] - df_display["Purchase Price"]
            df_display["P/L(%)"] = df_display["Difference"] / df_display["Purchase Price"] * 100
            df_display["P/L"] = df_display["Difference"] * df_display["Number of Shares"]

            # **Sort only for display**
            df_display_sorted = df_display.sort_values(by="P/L", ascending=False).reset_index(drop=True)

            fetch_complete.clear()

            # Print table
            print(df_display_sorted.to_string(formatters={
                "Purchase Price": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}",
                "Latest Price": lambda x: f"${x:,.2f}" if pd.notna(x) and x >= 0 else ("N/A" if pd.isna(x) else f"-${abs(x):,.2f}"),
                "Difference": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}",
                "P/L(%)": lambda x: f"{x:,.2f}%",
                "P/L": lambda x: f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}"
            }))

            # Totals
            if df_display["Latest Price"].notna().all():
                total_costs = (df_display["Purchase Price"] * df_display["Number of Shares"]).sum()
                total_current_value = (df_display["Latest Price"] * df_display["Number of Shares"]).sum()
                total_percentage_change = (total_current_value - total_costs) / total_costs * 100
                total_earnings = df_display["P/L"].sum()
                print(f"\nTotal Investment: ${total_costs:,.2f}")
                print(f"Total Current Value: ${total_current_value:,.2f}")
                print(f"Total Percentage Change: {total_percentage_change:,.2f}%")
                print(f"Total Profit: ${total_earnings:,.2f}" if total_earnings >= 0 else f"Total Loss: -${abs(total_earnings):,.2f}")

        threading.Event().wait(1)
except KeyboardInterrupt:
    print("\nExiting...")