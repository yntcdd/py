import flet as ft
import pandas as pd
import yfinance as yf
import time
import threading
from datetime import datetime

# Load portfolio
portfolio_df = pd.read_csv("my_portfolio.csv")
tickers_list = portfolio_df["Ticker"].tolist()

latest_prices = [None] * len(tickers_list)
lock = threading.Lock()
fetch_complete = threading.Event()

# Fetch thread (UNCHANGED LOGIC)
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
            fetch_complete.set()

        time.sleep(30)

threading.Thread(target=fetch_latest_price, daemon=True).start()

# Format helpers
def fmt_money(x):
    if x is None:
        return "N/A"
    return f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}"

def fmt_pct(x):
    return f"{x:,.2f}%"

def main(page: ft.Page):
    page.title = "Portfolio Tracker"
    page.padding = 20
    page.window_width = 1000
    page.window_height = 700

    # UI Elements
    clock_text = ft.Text(size=20, weight="bold")
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Ticker")),
            ft.DataColumn(ft.Text("Purchase Price")),
            ft.DataColumn(ft.Text("Latest Price")),
            ft.DataColumn(ft.Text("Difference")),
            ft.DataColumn(ft.Text("P/L (%)")),
            ft.DataColumn(ft.Text("P/L")),
        ],
        rows=[]
    )

    totals_text = ft.Text(size=16)

    page.add(
        clock_text,
        table,
        totals_text
    )

    df_display = portfolio_df.copy()
    df_display["Latest Price"] = [None] * len(df_display)

    def update_ui():
        while True:
            # update clock every second
            now = datetime.now()
            clock_text.value = f"Portfolio Performance - {now.strftime('%Y-%m-%d %H:%M:%S')}"

            # only update table when fetch is ready
            if fetch_complete.is_set():
                with lock:
                    df_display["Latest Price"] = latest_prices.copy()

                df_display["Difference"] = df_display["Latest Price"] - df_display["Purchase Price"]
                df_display["P/L(%)"] = df_display["Difference"] / df_display["Purchase Price"] * 100
                df_display["P/L"] = df_display["Difference"] * df_display["Number of Shares"]

                df_sorted = df_display.sort_values(by="P/L", ascending=False).reset_index(drop=True)

                # rebuild table
                rows = []
                for _, row in df_sorted.iterrows():
                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(row["Ticker"])),
                                ft.DataCell(ft.Text(fmt_money(row["Purchase Price"]))),
                                ft.DataCell(ft.Text(fmt_money(row["Latest Price"]))),
                                ft.DataCell(ft.Text(fmt_money(row["Difference"]))),
                                ft.DataCell(ft.Text(fmt_pct(row["P/L(%)"]))),
                                ft.DataCell(ft.Text(fmt_money(row["P/L"]))),
                            ]
                        )
                    )

                table.rows = rows

                # totals
                if df_display["Latest Price"].notna().all():
                    total_costs = (df_display["Purchase Price"] * df_display["Number of Shares"]).sum()
                    total_value = (df_display["Latest Price"] * df_display["Number of Shares"]).sum()
                    total_pct = (total_value - total_costs) / total_costs * 100
                    total_pl = df_display["P/L"].sum()

                    totals_text.value = (
                        f"Total Investment: {fmt_money(total_costs)}\n"
                        f"Total Value: {fmt_money(total_value)}\n"
                        f"Total Change: {fmt_pct(total_pct)}\n"
                        f"{'Total Profit' if total_pl >= 0 else 'Total Loss'}: {fmt_money(total_pl)}"
                    )

                fetch_complete.clear()

            page.update()
            time.sleep(1)

    threading.Thread(target=update_ui, daemon=True).start()

ft.app(target=main)