import pandas as pd
import yfinance as yf
import math
import time
import threading

# Load tickers
tickers_df = pd.read_csv('top_50_stocks.csv')
tickers_list = tickers_df["Ticker"].tolist()

# Currency conversion cache
# conversion_cache = {}

# def get_conversion_rate(from_currency, to_currency="USD"):
#     if from_currency == to_currency:
#         return 1
#     if from_currency in conversion_cache:
#         return conversion_cache[from_currency]

#     pair = f"{from_currency}{to_currency}=X"
#     hist = yf.Ticker(pair).history(period="1d")
#     if hist.empty:
#         rate = 1
#     else:
#         rate = hist["Close"].iloc[-1]

#     conversion_cache[from_currency] = rate
#     return rate

# Fetch latest prices
start = time.perf_counter()

tkrs = yf.Tickers(" ".join(tickers_list))
stocks_data = []

for symbol, tkr in tkrs.tickers.items():
    try:
        hist = tkr.history(period="1d")
        if hist.empty:
            continue

        latest_price = hist["Close"].iloc[-1]

        # info = tkr.info
        # currency = info.get("currency", "USD")
        # rate = get_conversion_rate(currency)
        rate = 1

        stocks_data.append({
            "Ticker": symbol,
            "Latest Price": latest_price * rate  # Convert to USD
        })

    except Exception:
        continue

df = pd.DataFrame(stocks_data)
end = time.perf_counter()
print(f"Fetch completed in {end - start:.2f} seconds\n")

# Sort by latest price
df = df.sort_values(by="Latest Price", ascending=False).reset_index(drop=True)

# Show top 10
df_top10 = df.head(10)
print("Top 10 Stocks by Latest Price (USD):")
print(df_top10.to_string(formatters={"Latest Price": "{:,.2f}".format}))
