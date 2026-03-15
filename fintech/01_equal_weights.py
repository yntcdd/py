## Equal Weights Strategy

import pandas as pd
import numpy as np
import yfinance as yf
import math

## Load the Stocks List

tickers = pd.read_csv('top_50_stocks.csv')
tickers.head()

def fetch_market_cap(ticker_list):
    data = yf.download(ticker_list, period = '1d', group_by = 'ticker', auto_adjust = False)
    
    stocks_data = []
    for ticker in ticker_list:
        latest_price = data[ticker]['Close'].iloc[-1]
        market_cap = yf.Ticker(ticker).info.get('marketCap', 'N/A')
        stocks_data.append({
            "Ticker" : ticker,
            "Market Cap" : market_cap,
            "Latest Price" : latest_price,
        })
        
    stocks_df = pd.DataFrame(stocks_data)
        
    return stocks_df

tickers_list = tickers["Ticker"].values.tolist()
df = fetch_market_cap(tickers_list)
df.head()

df = df.sort_values(by = "Market Cap", ascending = False)
df

## Taking Top 10 Stocks as per the market cap

df = df.head(10)
df.reset_index(inplace = True, drop = True)
df

portfolio_size = int(input("Enter the amount you want to invest: "))
position_size = portfolio_size / len(df.index)
position_size

df['Number of Shares to buy'] = df['Latest Price'].apply(lambda price: math.floor(
    position_size / price
))
df