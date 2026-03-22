import flet as ft
import pandas as pd
import yfinance as yf
import threading
import time
from datetime import datetime
from theme_config import LIGHT, DARK

portfolio_df = pd.read_csv("my_portfolio.csv")
tickers_list = portfolio_df["Ticker"].tolist()

latest_prices = [None] * len(tickers_list)
lock = threading.Lock()
fetch_complete = threading.Event()

# Sorting state
current_sort = "P/L"
sort_desc = True

def sort_df(df):
    return df.sort_values(by=current_sort, ascending=not sort_desc).reset_index(drop=True)

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
            print(fetch_complete.is_set())
        print("Fetched latest prices")
        time.sleep(30)

threading.Thread(target=fetch_latest_price, daemon=True).start()

def fmt_money(x):
    if x is None:
        return "N/A"
    return f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}"

def fmt_pct(x):
    return f"{x:,.2f}%"

def main(page: ft.Page):
    page.title = "Gotcha Portfolio"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 1000
    page.window.height = 1000
    page.window.left = 800
    page.window.top = 200
    page.scroll = ft.ScrollMode.AUTO

    # Refs
    clock_ref = ft.Ref[ft.Text]()
    table_ref = ft.Ref[ft.Column]()
    totals_ref = ft.Ref[ft.Container]()

    df_display = portfolio_df.copy()
    df_display["Current Price"] = [None] * len(df_display)


    def get_theme():
        return DARK if page.theme_mode == ft.ThemeMode.DARK else LIGHT
    
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon = ft.Icons.LIGHT_MODE
        
        table_ref.current.controls = build_table(sort_df(df_display))
        page.update()

    theme_btn = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        on_click=toggle_theme
    )

    def get_label(name):
        if name == current_sort:
            return f"{name} {'↓' if sort_desc else '↑'}"
        return name
        
    def change_sort(column):
        global current_sort, sort_desc

        if current_sort == column:
            sort_desc = not sort_desc
        else:
            current_sort = column
            sort_desc = True

        table_ref.current.controls = build_table(sort_df(df_display))
        page.update()

    def build_table(df):
        rows = []

        for _, row in df.iterrows():
            pl = row["P/L"]
            color = get_theme()["green"] if pl >= 0 else get_theme()["red"]

            rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(row["Ticker"], width=80),
                        ft.Text(fmt_money(row["Purchase Price"]), width=120, color=get_theme()["orange"], weight=ft.FontWeight.BOLD),
                        ft.Text(fmt_money(row["Current Price"]), width=120, color=get_theme()["purple"], weight=ft.FontWeight.BOLD),
                        ft.Text(fmt_money(row["Difference"]), width=120, color=color),
                        ft.Text(fmt_pct(row["P/L(%)"]), width=120, color=color),
                        ft.Text(fmt_money(pl), width=120, color=color),
                    ], spacing=10),
                    padding=10,
                    border_radius=8,
                    bgcolor=get_theme()["card"]
                )
            )

        return rows

    def update_ui():
        while True:
            now = datetime.now()
            clock_ref.current.value = f"Portfolio Performance - {now.strftime('%Y-%m-%d %H:%M:%S')}"

            if fetch_complete.is_set():
                print("Updating UI with latest prices...")
                with lock:
                    df_display["Current Price"] = latest_prices.copy()

                df_display["Difference"] = df_display["Current Price"] - df_display["Purchase Price"]
                df_display["P/L(%)"] = df_display["Difference"] / df_display["Purchase Price"] * 100
                df_display["P/L"] = df_display["Difference"] * df_display["Number of Shares"]

                df_sorted = sort_df(df_display)

                table_ref.current.controls = build_table(df_sorted)

                if df_display["Current Price"].notna().all():
                    total_cost = (df_display["Purchase Price"] * df_display["Number of Shares"]).sum()
                    total_val = (df_display["Current Price"] * df_display["Number of Shares"]).sum()
                    total_pl = df_display["P/L"].sum()
                    total_pct = (total_val - total_cost) / total_cost * 100

                    totals_ref.current.content = ft.Row([
                        build_stat_card("Investment", fmt_money(total_cost), get_theme()["accent"]),
                        build_stat_card("Value", fmt_money(total_val), get_theme()["purple"]),
                        build_stat_card("Change", fmt_pct(total_pct),
                                        get_theme()["green"] if total_pct >= 0 else get_theme()["red"]),
                        build_stat_card("P/L", fmt_money(total_pl),
                                        get_theme()["green"] if total_pl >= 0 else get_theme()["red"]),
                    ], spacing=10)

                fetch_complete.clear()

            print("UI Updated")
            page.update()
            time.sleep(1)

    def build_stat_card(title, value, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=12),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=color),
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, color),
            border_radius=10,
            expand=True
        )

    # UI Layout
    page.add(
        ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("Gotcha Portfolio Tracker", size=30, weight=ft.FontWeight.BOLD),
                        ft.Text("Live portfolio tracking with real-time updates", size=14),
                    ], horizontal_alignment=ft.CrossAxisAlignment.START, expand=True),
                    theme_btn
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(bottom=20)
            ),

            ft.Text(ref=clock_ref, size=16, weight=ft.FontWeight.BOLD),

            ft.Container(
                ref=totals_ref,
                padding=10
            ),

            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.TextButton(get_label("Ticker"), width=80, on_click=lambda e: change_sort("Ticker")),
                        ft.TextButton(get_label("Purchase Price"), width=120, on_click=lambda e: change_sort("Purchase Price")),
                        ft.TextButton(get_label("Current Price"), width=120, on_click=lambda e: change_sort("Current Price")),
                        ft.TextButton(get_label("Difference"), width=120, on_click=lambda e: change_sort("Difference")),
                        ft.TextButton(get_label("P/L(%)"), width=120, on_click=lambda e: change_sort("P/L(%)")),
                        ft.TextButton(get_label("P/L"), width=120, on_click=lambda e: change_sort("P/L")),
                    ]),
                    ft.Divider(),
                    ft.Column(ref=table_ref, spacing=5)
                ]),
                padding=15,
                border=ft.Border.all(2, ft.Colors.GREY_300),
                border_radius=10
            )
        ], spacing=15)
    )

    # threading.Thread(target=update_ui, daemon=True).start()
    # update_ui()


if __name__ == "__main__":
    ft.run(main)
    