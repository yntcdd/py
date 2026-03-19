## Equal Weights Strategy

import pandas as pd
import numpy as np
import yfinance as yf
import math
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Load the Stocks List
tickers = pd.read_csv('top_50_stocks.csv')

def get_conversion_rate(from_currency, to_currency, cache, lock):
    if from_currency == to_currency:
        return 1

    with lock:
        if from_currency in cache:
            return cache[from_currency]

    pair = f"{from_currency}{to_currency}=X"
    hist = yf.Ticker(pair).history(period="1d")

    if hist.empty:
        return 1

    rate = hist["Close"].iloc[-1]

    with lock:
        cache[from_currency] = rate

    return rate

def fetch_market_cap(ticker_list):
    stocks_data = []
    conversion_cache = {}
    lock = threading.Lock()

    def process_ticker(ticker):
        try:
            tkr = yf.Ticker(ticker)

            # Get latest price
            hist = tkr.history(period="1d")
            if hist.empty:
                return

            latest_price = hist["Close"].iloc[-1]

            # Get info
            info = tkr.info

            currency = info.get("currency", "USD")
            rate = get_conversion_rate(currency, "USD", conversion_cache, lock)

            market_cap = info.get("marketCap")
            if market_cap is not None:
                market_cap *= rate

            result = {
                "Ticker": ticker,
                "Market Cap": market_cap,
                "Latest Price": latest_price * rate,
            }

            with lock:
                stocks_data.append(result)

        except Exception:
            return

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(process_ticker, ticker_list)

    return pd.DataFrame(stocks_data)

start = time.perf_counter()

tickers_list = tickers["Ticker"].values.tolist()
df = fetch_market_cap(tickers_list)

end = time.perf_counter()

print(f"Fetch completed in {end - start:.2f} seconds")

# Clean + sort
df = df.sort_values(by="Market Cap", ascending=False)

print("This is the Stocks List:")
print("-----------------------")
print(df.to_string(formatters={
    "Market Cap": "{:,.0f}".format,
    "Latest Price": "{:,.2f}".format
}))
print()

# Top 10
df_top10 = df.head(10).reset_index(drop=True)

print("This is the Top 10 Stocks as per the Market Cap:")
print("-----------------------")
print(df_top10.to_string(formatters={
    "Market Cap": "{:,.0f}".format,
    "Latest Price": "{:,.2f}".format
}))
print()

# Portfolio calculation
portfolio_size = int(input("Enter the amount you want to invest: "))
position_size = portfolio_size / len(df_top10.index)

print(f"Each position size: ${position_size:,.2f}")

df_top10['Number of Shares to buy'] = df_top10['Latest Price'].apply(
    lambda price: math.floor(position_size / price)
)

print("This is how many shares you need to buy:")
print("-----------------------")
print(df_top10.to_string(formatters={
    "Market Cap": "{:,.0f}".format,
    "Latest Price": "{:,.2f}".format,
    "Number of Shares to buy": "{:,.0f}".format
}))