## Value Investing

import pandas as pd
import numpy as np
import yfinance as yf
import math
from scipy import stats
from statistics import mean

## Load the Tickers
tickers = pd.read_csv('top_50_stocks.csv')
# print(tickers.head())

def fetch_values_of_stocks(tickers):
    
    value_cols = [
        "Ticker", 
        "Price", 
        "PE-Ratio", 
        "PB-Ratio", 
        "PS-Ratio", 
        "EV/EBITDA", 
        "EV/GP"
    ]
    
    value_df = pd.DataFrame(columns=value_cols)
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        price = stock.history(period = "1d")['Close'].iloc[-1]
        
        financials = stock.financials
        balanceSheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        pe_ratio = stock.info.get("forwardPE", np.nan)
        pb_ratio = stock.info.get("priceToBook", np.nan)
        ps_ratio = stock.info.get("priceToSalesTrailing12Months", np.nan)
        ev = stock.info.get("enterpriseValue", np.nan)
        ebitda = stock.info.get("ebitda", np.nan)
        evEbitda = ev / ebitda if ev and ebitda else np.nan
        grossProfit = stock.info.get("grossMargins", np.nan) * stock.info.get("totalRevenue", np.nan)
        evGrossProfit = ev / grossProfit if ev and grossProfit else np.nan
        
        value_df.loc[len(value_df)] = [
            ticker, 
            price, 
            pe_ratio, 
            pb_ratio, 
            ps_ratio, 
            evEbitda, 
            evGrossProfit
        ]
        
    return value_df

tickers_list = tickers['Ticker'].values.tolist()

df = fetch_values_of_stocks(tickers_list)
print(df)

print(df.info())

## Take care of Null Values

value_cols = [
        "PE-Ratio", 
        "PB-Ratio", 
        "PS-Ratio", 
        "EV/EBITDA", 
        "EV/GP"
    ]

for col in value_cols:
    df[col] = df[col].fillna(df[col].mean())
    
print(df.info())

percentile_metrics = {
    "PE-Ratio" : "PE-Ratio_Percentile", 
    "PB-Ratio" : "PB-Ratio_Percentile",
    "PS-Ratio" : "PS-Ratio_Percentile",
    "EV/EBITDA" : "EV/EBITDA_Percentile",
    "EV/GP" : "EV/GP_Percentile"
}


for metric, percentile in percentile_metrics.items():
    df[percentile] = df[metric].apply(lambda x: stats.percentileofscore(df[metric], x) / 100)

df.head()

df['Value Score'] = df[[value for value in percentile_metrics.values()]].mean(axis = 1)
print(df)

df = df.sort_values(by="Value Score", ascending=False)
print(df)

df.head(10)
