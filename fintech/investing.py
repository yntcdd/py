import pandas as pd
import numpy as np
import yfinance as yf
import math
import time
from scipy import stats

tickers = pd.read_csv('top_50_stocks.csv')
tickers_list = tickers["Ticker"].values.tolist()

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
    return pd.DataFrame(stocks_data)

start = time.perf_counter()
df_equal = fetch_market_cap(tickers_list)
end = time.perf_counter()

df_equal = df_equal.sort_values(by="Market Cap", ascending=False)
df_equal["Market Cap"] = df_equal["Market Cap"].map('{:,.0f}'.format)
df_equal["Latest Price"] = df_equal["Latest Price"].map('{:,.2f}'.format)

df_top10 = df_equal.head(10).reset_index(drop=True)

portfolio_size = int(input())
position_size = portfolio_size / len(df_top10.index)

latest_price_float = df_top10["Latest Price"].str.replace(",", "").astype(float)
df_top10['Number of Shares to buy'] = latest_price_float.apply(lambda price: math.floor(position_size / price))

def fetch_values_of_stocks(tickers):
    value_cols = [
        "Ticker", "Price", "PE-Ratio", "PB-Ratio",
        "PS-Ratio", "EV/EBITDA", "EV/GP"
    ]
    value_df = pd.DataFrame(columns=value_cols)
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'].iloc[-1]
        pe_ratio = stock.info.get("forwardPE", np.nan)
        pb_ratio = stock.info.get("priceToBook", np.nan)
        ps_ratio = stock.info.get("priceToSalesTrailing12Months", np.nan)
        ev = stock.info.get("enterpriseValue", np.nan)
        ebitda = stock.info.get("ebitda", np.nan)
        evEbitda = ev / ebitda if ev and ebitda else np.nan
        grossProfit = stock.info.get("grossMargins", np.nan) * stock.info.get("totalRevenue", np.nan)
        evGrossProfit = ev / grossProfit if ev and grossProfit else np.nan
        value_df.loc[len(value_df)] = [
            ticker, price, pe_ratio, pb_ratio, ps_ratio, evEbitda, evGrossProfit
        ]
    return value_df

df_value = fetch_values_of_stocks(tickers_list)

value_cols = ["PE-Ratio", "PB-Ratio", "PS-Ratio", "EV/EBITDA", "EV/GP"]
for col in value_cols:
    df_value[col] = df_value[col].fillna(df_value[col].mean())

percentile_metrics = {
    "PE-Ratio": "PE Percentile",
    "PB-Ratio": "PB Percentile",
    "PS-Ratio": "PS Percentile",
    "EV/EBITDA": "EV/EBITDA Percentile",
    "EV/GP": "EV/GP Percentile"
}

for metric, percentile in percentile_metrics.items():
    df_value[percentile] = df_value[metric].apply(
        lambda x: stats.percentileofscore(df_value[metric], x) / 100
    )

df_value['Value Score'] = df_value[list(percentile_metrics.values())].mean(axis=1)
df_value = df_value.sort_values(by="Value Score", ascending=False)
df_value_top10 = df_value.head(10)

def create_dividend_df(tickers):
    columns = [
        "Ticker", "Dividend Yield(%)", "Dividend Rate",
        "Payout Ratio(%)", "5 Year Avg Dividend Yield(%)", "Earning Growth(%)"
    ]
    dividend_df = pd.DataFrame(columns=columns)
    for stock in tickers:
        ticker = yf.Ticker(stock)
        info = ticker.info
        dividend_yield = info.get("dividendYield", np.nan)
        dividend_yield = dividend_yield * 100 if dividend_yield else np.nan
        dividend_rate = info.get("dividendRate", np.nan)
        payout_ratio = info.get("payoutRatio", np.nan)
        payout_ratio = payout_ratio * 100 if payout_ratio else np.nan
        five_year = info.get("fiveYearAvgDividendYield", np.nan)
        five_year = five_year * 100 if five_year else np.nan
        growth = info.get("earningsGrowth", np.nan)
        growth = growth * 100 if growth else np.nan
        dividend_df.loc[len(dividend_df)] = [
            stock, dividend_yield, dividend_rate, payout_ratio, five_year, growth
        ]
    numeric_cols = columns[1:]
    for col in numeric_cols:
        if col == "Payout Ratio(%)":
            dividend_df[col + " Norm"] = 1 - (dividend_df[col] - dividend_df[col].min()) / (dividend_df[col].max() - dividend_df[col].min())
        else:
            dividend_df[col + " Norm"] = (dividend_df[col] - dividend_df[col].min()) / (dividend_df[col].max() - dividend_df[col].min())
    return dividend_df

dividend_df = create_dividend_df(tickers_list)

weights = {
    "Dividend Yield(%) Norm": 0.3,
    "Dividend Rate Norm": 0.2,
    "Payout Ratio(%) Norm": 0.2,
    "5 Year Avg Dividend Yield(%) Norm": 0.2,
    "Earning Growth(%) Norm": 0.1
}

dividend_df["Dividend Score"] = dividend_df[list(weights.keys())].mul(list(weights.values())).sum(axis=1)
dividend_df = dividend_df.sort_values(by="Dividend Score", ascending=False)
df_dividend_top10 = dividend_df.head(10)

output_file = "investment_strategies.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_top10.to_excel(writer, sheet_name="Equal Weight", index=False)
    df_value_top10.to_excel(writer, sheet_name="Value Investing", index=False)
    df_dividend_top10.to_excel(writer, sheet_name="Dividend Investing", index=False)

print(output_file)