## Equal Weights Strategy

import pandas as pd
import numpy as np
import yfinance as yf
import math

# Load the Stocks List
tickers = pd.read_csv('top_50_stocks.csv')

def get_conversion_rate(from_currency, to_currency, cache):
    if from_currency == to_currency:
        return 1
    if from_currency in cache:
        return cache[from_currency]

    pair = f"{from_currency}{to_currency}=X"
    hist = yf.Ticker(pair).history(period="1d")
    if hist.empty:
        return 1

    rate = hist["Close"].iloc[-1]
    cache[from_currency] = rate
    return rate

def fetch_market_cap(ticker_list):
    data = yf.download(ticker_list, period='1d', group_by='ticker', auto_adjust=False)
    
    stocks_data = []
    conversion_cache = {}
    
    for ticker in ticker_list:
        latest_price = data[ticker]['Close'].iloc[-1]
        info = yf.Ticker(ticker).info
        
        currency = info.get("currency", "USD")
        rate = get_conversion_rate(currency, "USD", conversion_cache)
        
        market_cap = info.get("marketCap")
        if market_cap is not None:
            market_cap *= rate
        
        stocks_data.append({
            "Ticker": ticker,
            "Market Cap": market_cap,
            "Latest Price": latest_price * rate,
        })
    
    stocks_df = pd.DataFrame(stocks_data)
    return stocks_df

tickers_list = tickers["Ticker"].values.tolist()
df = fetch_market_cap(tickers_list)

# Sort by market cap
df = df.sort_values(by="Market Cap", ascending=False)

# Format Market Cap as int with commas, Latest Price with 2 decimals
df["Market Cap"] = df["Market Cap"].map('{:,.0f}'.format)
df["Latest Price"] = df["Latest Price"].map('{:,.2f}'.format)

print("This is the Stocks List:")
print("-----------------------")
print(df)
print()

# Top 10 stocks by market cap
df_top10 = df.head(10).reset_index(drop=True)
print("This is the Top 10 Stocks as per the Market Cap:")
print("-----------------------")
print(df_top10)
print()

# Portfolio calculation
portfolio_size = int(input("Enter the amount you want to invest: "))
position_size = portfolio_size / len(df_top10.index)
print(f"Each position size: ${position_size:,.2f}")

# Calculate number of shares to buy (using unformatted Latest Price)
# Need to convert Latest Price back to float for calculation
latest_price_float = df_top10["Latest Price"].str.replace(",", "").astype(float)
df_top10['Number of Shares to buy'] = latest_price_float.apply(lambda price: math.floor(position_size / price))

print("This is how many shares you need to buy:")
print("-----------------------")
print(df_top10)