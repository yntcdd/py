## Dividend Based Stock Selection Strategy

import pandas as pd
import numpy as np
import yfinance as yf
import math
from scipy import stats
from statistics import mean
import threading
import time

## Load the Tickers
tickers = pd.read_csv('top_50_stocks.csv')
# print(tickers.head())

## Weighted Scoring Model for finding the final score

def create_dividend_df(tickers):
    columns = [
        "Ticker",
        "Dividend Yield(%)",
        "Dividend Rate",
        "Payout Ratio(%)",
        "5 Year Avg Dividend Yield(%)",
        "Earning Growth(%)"
    ]
    
    dividend_df = pd.DataFrame(columns =  columns)
    
    for stock in tickers:
        ticker = yf.Ticker(stock)
        info = ticker.info
        
        dividend_yield = info.get("dividendYield", np.nan) * 100 if info.get("dividendYield") else np.nan
        dividend_rate = info.get("dividendRate", np.nan)
        payout_ratio = info.get("payoutRatio", np.nan) * 100 if info.get("dividendYield") else np.nan
        five_year_avg_dividend_yield = info.get("fiveYearAvgDividendYield", np.nan) * 100 if info.get("dividendYield") else np.nan
        earning_growth = info.get("earningsGrowth", np.nan) * 100 if info.get("earningsGrowth") else np.nan
        
        dividend_df.loc[len(dividend_df)] = [
            stock,
            dividend_yield,
            dividend_rate,
            payout_ratio,
            five_year_avg_dividend_yield,
            earning_growth
        ]
        
    ## We have got our df with dividend information
    numeric_cols = [
        "Dividend Yield(%)",
        "Dividend Rate",
        "Payout Ratio(%)",
        "5 Year Avg Dividend Yield(%)",
        "Earning Growth(%)"
    ]
    
    for col in numeric_cols:
        if col == "Payout Ratio(%)":
            dividend_df[col + " Normalized"] = 1 - (dividend_df[col] - dividend_df[col].min()) / (dividend_df[col].max() - dividend_df[col].min())
        else:
            dividend_df[col + " Normalized"] = (dividend_df[col] - dividend_df[col].min()) / (dividend_df[col].max() - dividend_df[col].min())
        
    return dividend_df

tickers_list = tickers["Ticker"].values.tolist()
dividend_df = create_dividend_df(tickers_list)
# print(dividend_df)

weights = {
    "Dividend Yield(%) Normalized": 0.3,
    "Dividend Rate Normalized": 0.2,
    "Payout Ratio(%) Normalized": 0.2,
    "5 Year Avg Dividend Yield(%) Normalized": 0.2,
    "Earning Growth(%) Normalized": 0.1
}

dividend_df["Dividend Score"] = dividend_df[[col for col in weights.keys()]].mul(list(weights.values())).sum(axis = 1)
# print(dividend_df)

dividend_df = dividend_df.sort_values(by = "Dividend Score", ascending = False)
print(dividend_df)