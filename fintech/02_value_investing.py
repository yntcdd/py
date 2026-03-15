## Value Investing

import pandas as pd
import numpy as np
import yfinance as yf
import math
from pprint import pprint

tickers = pd.read_csv('top_50_stocks.csv')
# print(tickers.head())

def fetch_values_of_stocks(tickers):
    
    value_cols = [
        "Ticker",
        "Price",
        "PE-Ratio",
        "PB-Ratio",
        "PS-Ration",
        "EV/EBITDA",
        "EV/GP"
    ]
    
    value_df = pd.DataFrame(columns=value_cols)
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        price = stock.history(period = "1d")

ril = yf.Ticker("RELIANCE.NS")
# pprint(ril.info)