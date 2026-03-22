import asyncio
import flet as ft
import flet_charts as fch
import pandas as pd
import yfinance as yf
from datetime import datetime
from theme_config import LIGHT, DARK

portfolio_df = pd.read_csv("my_portfolio.csv")
tickers_list = portfolio_df["Ticker"].tolist()

latest_prices  = [None] * len(tickers_list)
fetch_complete = asyncio.Event()

portfolio_history: list[tuple[str, float]] = []
history_ready  = asyncio.Event()

current_sort = "P/L"
sort_desc    = True

def sort_df(df):
    return df.sort_values(by=current_sort, ascending=not sort_desc).reset_index(drop=True)

async def fetch_latest_price():
    global latest_prices
    while True:
        try:
            def _fetch():
                tkrs = yf.Tickers(" ".join(tickers_list))
                temp = []
                for symbol, tkr in tkrs.tickers.items():
                    try:
                        hist = tkr.history(period="1d")
                        temp.append(hist["Close"].iloc[-1] if not hist.empty else 0)
                    except Exception:
                        temp.append(0)
                return temp
            prices = await asyncio.get_event_loop().run_in_executor(None, _fetch)
            latest_prices = prices
            fetch_complete.set()
        except Exception as e:
            print(f"Live fetch error: {e}")
        await asyncio.sleep(30)

async def fetch_portfolio_history():
    global portfolio_history
    try:
        start = "2025-02-03"
        def _fetch():
            rows = {}
            for _, holding in portfolio_df.iterrows():
                ticker = holding["Ticker"]
                shares = holding["Number of Shares"]
                tkr    = yf.Ticker(ticker)
                hist   = tkr.history(start=start)
                if hist.empty:
                    continue
                for ts, row in hist.iterrows():
                    day = ts.strftime("%Y-%m-%d")
                    rows.setdefault(day, 0.0)
                    rows[day] += row["Close"] * shares
            return sorted(rows.items())
        data = await asyncio.get_event_loop().run_in_executor(None, _fetch)
        portfolio_history = data
        history_ready.set()
        print(f"History fetched: {len(data)} trading days")
    except Exception as e:
        print(f"History fetch error: {e}")

def fmt_money(x):
    if x is None:
        return "N/A"
    return f"${x:,.2f}" if x >= 0 else f"-${abs(x):,.2f}"

def fmt_pct(x):
    return f"{x:,.2f}%"

RANGE_MAP = {
    "1 week":  ("7d",  "1d"),
    "2 weeks": ("14d", "1d"),
    "30 days": ("1mo", "1d"),
    "90 days": ("3mo", "1d"),
    "1 year":  ("1y",  "1wk"),
    "5 years": ("5y",  "1mo"),
}

async def main(page: ft.Page):
    page.title       = "Gotcha Portfolio"
    page.theme_mode  = ft.ThemeMode.LIGHT
    page.padding     = 0
    page.window.width  = 1200
    page.window.height = 900
    page.window.left   = 100
    page.window.top    = 100

    clock_ref       = ft.Ref[ft.Text]()
    table_ref       = ft.Ref[ft.Column]()
    totals_ref      = ft.Ref[ft.Container]()
    perf_chart_ref  = ft.Ref[ft.Container]()
    alloc_chart_ref = ft.Ref[ft.Container]()
    stock_symbol    = ft.Ref[ft.TextField]()
    chart_container = ft.Ref[ft.Container]()
    price_info      = ft.Ref[ft.Container]()
    error_messages  = ft.Ref[ft.Container]()
    time_range_dd   = ft.Ref[ft.Dropdown]()

    df_display = portfolio_df.copy()
    df_display["Current Price"] = [None] * len(df_display)

    def get_theme():
        return DARK if page.theme_mode == ft.ThemeMode.DARK else LIGHT
    
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon  = ft.Icons.DARK_MODE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon  = ft.Icons.LIGHT_MODE

        if table_ref.current:
            table_ref.current.controls = build_table(sort_df(df_display))

        # Rebuild allocation chart so legend text picks up new theme colors
        if alloc_chart_ref.current:
            alloc_chart_ref.current.content = build_alloc_chart(df_display)

        page.update()

    theme_btn = ft.IconButton(icon=ft.Icons.LIGHT_MODE, on_click=toggle_theme)

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
            sort_desc    = True
        if table_ref.current:
            table_ref.current.controls = build_table(sort_df(df_display))
        page.update()

    def build_table(df):
        rows = []
        for _, row in df.iterrows():
            pl    = row["P/L"]
            color = get_theme()["green"] if pl >= 0 else get_theme()["red"]
            rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(row["Ticker"],                    width=70,  size=13),
                        ft.Text(fmt_money(row["Purchase Price"]), width=110, size=13, color=get_theme()["orange"], weight=ft.FontWeight.BOLD),
                        ft.Text(fmt_money(row["Current Price"]),  width=110, size=13, color=get_theme()["purple"], weight=ft.FontWeight.BOLD),
                        ft.Text(fmt_money(row["Difference"]),     width=110, size=13, color=color),
                        ft.Text(fmt_pct(row["P/L(%)"]),           width=100, size=13, color=color),
                        ft.Text(fmt_money(pl),                    width=100, size=13, color=color),
                    ], spacing=10),
                    padding=7,
                    border_radius=6,
                    bgcolor=get_theme()["card"],
                )
            )
        return rows

    def build_stat_card(title, value, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=12),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=color),
            ], spacing=5),
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, color),
            border_radius=10,
            expand=True,
        )

    def build_perf_chart():
        if not portfolio_history:
            return ft.Container(
                content=ft.Text("Fetching history from Feb 3...",
                                italic=True, color=ft.Colors.GREY_500, size=12),
                height=220, alignment=ft.alignment.center,
            )

        values = [v for _, v in portfolio_history]
        dates  = [d for d, _ in portfolio_history]
        theme  = get_theme()
        n      = len(values)

        is_up      = values[-1] >= values[0]
        line_color = theme["green"] if is_up else theme["red"]
        fill_color = ft.Colors.with_opacity(0.10, line_color)

        y_min   = min(values)
        y_max   = max(values)
        y_range = y_max - y_min
        y_pad   = y_range * 0.05

        chart_min_y = y_min - y_pad
        chart_max_y = y_max + y_pad
        y_mid       = (y_min + y_max) / 2

        left_labels = [
            fch.ChartAxisLabel(
                value=chart_min_y,
                label=ft.Container(
                    ft.Text(f"${y_min/1000:.1f}k", size=9, color=theme["subtext"]),
                    padding=ft.Padding.only(right=4),
                ),
            ),
            fch.ChartAxisLabel(
                value=y_mid,
                label=ft.Container(
                    ft.Text(f"${y_mid/1000:.1f}k", size=9, color=theme["subtext"]),
                    padding=ft.Padding.only(right=4),
                ),
            ),
            fch.ChartAxisLabel(
                value=chart_max_y,
                label=ft.Container(
                    ft.Text(f"${y_max/1000:.1f}k", size=9, color=theme["subtext"]),
                    padding=ft.Padding.only(right=4),
                ),
            ),
        ]

        x_indices     = [0, round((n - 1) / 2), n - 1]
        bottom_labels = [
            fch.ChartAxisLabel(
                value=float(idx),
                label=ft.Container(
                    ft.Text(dates[idx][5:], size=9, color=theme["subtext"]),
                    padding=ft.Padding.only(top=4),
                ),
            )
            for idx in x_indices
        ]

        data_points = [
            fch.LineChartDataPoint(
                float(i), values[i],
                tooltip=f"{dates[i]}  ${values[i]:,.0f}",
            )
            for i in range(n)
        ]

        chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=data_points,
                    stroke_width=2.5,
                    color=line_color,
                    below_line_bgcolor=fill_color,
                    curved=True,
                    rounded_stroke_cap=True,
                ),
            ],
            left_axis=fch.ChartAxis(
                labels=left_labels,
                label_size=62,
                show_labels=True,
            ),
            bottom_axis=fch.ChartAxis(
                labels=bottom_labels,
                label_size=30,
                show_labels=True,
            ),
            min_y=chart_min_y,
            max_y=chart_max_y,
            min_x=0.0,
            max_x=float(n - 1),
            expand=True,
        )
        return ft.Container(content=chart, height=220, expand=True)

    def build_alloc_chart(df):
        if df["Current Price"].isna().any():
            return ft.Container(
                content=ft.Text("Waiting for price data...",
                                italic=True, color=ft.Colors.GREY_500, size=12),
                alignment=ft.alignment.center,
            )

        theme  = get_theme()
        colors = theme["chart"]

        df = df.copy()
        df["Value"] = df["Current Price"] * df["Number of Shares"]
        total = df["Value"].sum()
        df["Pct"] = df["Value"] / total * 100

        df_sorted = df.sort_values("Value", ascending=False).reset_index(drop=True)
        top6      = df_sorted.head(6)
        rest      = df_sorted.iloc[6:]

        sections     = []
        legend_items = []

        for i, (_, row) in enumerate(top6.iterrows()):
            color = colors[i % len(colors)]
            pct   = row["Pct"]
            val   = row["Value"]
            sections.append(fch.PieChartSection(
                value=pct,
                title=f"{pct:.0f}%" if pct >= 6 else "",
                title_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD, color=theme["text"]),
                color=color,
                radius=54,
                border_side=ft.BorderSide(2, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
            ))
            legend_items.append(
                ft.Row([
                    ft.Container(width=11, height=11, bgcolor=color, border_radius=3),
                    ft.Column([
                        ft.Text(row["Ticker"], size=12, weight=ft.FontWeight.W_600,
                                color=theme["text"]),          # uses live theme
                        ft.Text(fmt_money(val), size=10,
                                color=theme["subtext"]),       # uses live theme
                    ], spacing=0, tight=True, expand=True),
                    ft.Text(f"{pct:.1f}%", size=11, weight=ft.FontWeight.BOLD,
                            color=color),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        if not rest.empty:
            other_pct   = rest["Pct"].sum()
            other_val   = rest["Value"].sum()
            other_color = theme["chart_other"]
            sections.append(fch.PieChartSection(
                value=other_pct,
                title=f"{other_pct:.0f}%" if other_pct >= 6 else "",
                title_style=ft.TextStyle(size=10, weight=ft.FontWeight.BOLD, color=theme["text"]),
                color=other_color,
                radius=54,
                border_side=ft.BorderSide(2, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
            ))
            legend_items.append(
                ft.Row([
                    ft.Container(width=11, height=11, bgcolor=other_color, border_radius=3),
                    ft.Column([
                        ft.Text("Other", size=12, weight=ft.FontWeight.W_600,
                                color=theme["text"]),          # uses live theme
                        ft.Text(fmt_money(other_val), size=10,
                                color=theme["subtext"]),       # uses live theme
                    ], spacing=0, tight=True, expand=True),
                    ft.Text(f"{other_pct:.1f}%", size=11, weight=ft.FontWeight.BOLD,
                            color=other_color),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )

        return ft.Row([
            fch.PieChart(
                sections=sections,
                sections_space=3,
                center_space_radius=34,
                width=160,
                height=220,
            ),
            ft.Column(
                legend_items,
                spacing=8,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    async def fetch_stock_data(e):
        symbol     = stock_symbol.current.value.upper().strip()
        time_range = time_range_dd.current.value or "30 days"
        period, interval = RANGE_MAP[time_range]

        if not symbol:
            error_messages.current.content = ft.Text(
                "Please enter a stock symbol.", color=get_theme()["red"], size=14)
            error_messages.current.visible  = True
            price_info.current.visible      = False
            chart_container.current.visible = False
            page.update()
            return

        error_messages.current.visible  = False
        price_info.current.visible      = False
        chart_container.current.content = ft.Text(
            "Loading stock data...", size=16, color=get_theme()["accent"], italic=True)
        chart_container.current.visible = True
        page.update()

        try:
            def _fetch():
                return yf.Ticker(symbol).history(period=period, interval=interval)

            hist = await asyncio.get_event_loop().run_in_executor(None, _fetch)

            if hist.empty:
                raise ValueError(f"No data found for '{symbol}'.")

            closes      = hist["Close"].tolist()
            dates       = [d.strftime("%b %d") for d in hist.index]
            latest_date = hist.index[-1].strftime("%Y-%m-%d")

            def price_card(label, value, txt_color, bg_color):
                return ft.Container(
                    content=ft.Column([
                        ft.Text(label, size=12, color=get_theme()["bg"]),
                        ft.Text(f"${value:.2f}", size=18,
                                weight=ft.FontWeight.BOLD, color=txt_color),
                    ], spacing=4),
                    padding=12, bgcolor=bg_color, border_radius=10, expand=True,
                )

            price_info.current.content = ft.Column([
                ft.Row([
                    ft.Text(symbol, size=22, weight=ft.FontWeight.BOLD,
                            color=get_theme()["accent"]),
                    ft.Text(latest_date, size=13, color=get_theme()["subtext"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1),
                ft.Row([
                    price_card("Open",  hist["Open"].iloc[-1],  get_theme()["card"], get_theme()["accent"]),
                    price_card("High",  hist["High"].iloc[-1],  get_theme()["card"], get_theme()["green"]),
                    price_card("Low",   hist["Low"].iloc[-1],   get_theme()["card"], get_theme()["red"]),
                    price_card("Close", closes[-1],             get_theme()["card"], get_theme()["purple"]),
                ], spacing=8),
            ], spacing=8)
            price_info.current.visible = True

            step = max(1, len(closes) // 6)
            bottom_labels = [
                fch.ChartAxisLabel(
                    value=float(i),
                    label=ft.Container(ft.Text(dates[i], size=10), padding=ft.Padding.only(top=4)),
                )
                for i in range(0, len(closes), step)
            ]

            chart = fch.LineChart(
                data_series=[fch.LineChartData(
                    points=[fch.LineChartDataPoint(float(i), closes[i])
                            for i in range(len(closes))],
                    stroke_width=2.5,
                    color=ft.Colors.ORANGE,
                    below_line_bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ORANGE),
                    curved=True,
                    rounded_stroke_cap=True,
                )],
                left_axis=fch.ChartAxis(label_size=55),
                bottom_axis=fch.ChartAxis(labels=bottom_labels, label_size=32),
                min_y=min(closes) * 0.97,
                max_y=max(closes) * 1.03,
                min_x=0.0,
                max_x=float(len(closes) - 1),
                expand=True,
            )

            chart_container.current.content = ft.Container(
                content=ft.Column([
                    ft.Text(f"Closing Price - {time_range} ({symbol})",
                            size=15, weight=ft.FontWeight.BOLD),
                    chart,
                ], spacing=10),
                padding=15,
                border=ft.Border.all(2, ft.Colors.GREY_300),
                border_radius=10,
            )

        except Exception as ex:
            error_messages.current.content = ft.Text(
                f"Error: {ex}", color=ft.Colors.RED, size=13)
            error_messages.current.visible  = True
            price_info.current.visible      = False
            chart_container.current.content = ft.Text("")

        page.update()

    def build_portfolio_tab():
        return ft.Column([
            ft.Text(ref=clock_ref, size=13, color=ft.Colors.GREY_600),
            ft.Container(ref=totals_ref, padding=ft.Padding.symmetric(vertical=4)),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Portfolio Performance",
                                size=13, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            ref=perf_chart_ref,
                            content=ft.Text("Fetching history...", italic=True,
                                            size=12, color=ft.Colors.GREY_500),
                            height=220,
                        ),
                    ], spacing=8),
                    padding=14,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    expand=3,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Allocation (Top 6 + Other)",
                                size=13, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            ref=alloc_chart_ref,
                            content=ft.Text("Waiting for prices...", italic=True,
                                            size=12, color=ft.Colors.GREY_500),
                            height=220,
                        ),
                    ], spacing=8),
                    padding=14,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    expand=2,
                ),
            ], spacing=12),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.TextButton(get_label("Ticker"),         width=70,  on_click=lambda e: change_sort("Ticker")),
                        ft.TextButton(get_label("Purchase Price"), width=110, on_click=lambda e: change_sort("Purchase Price")),
                        ft.TextButton(get_label("Current Price"),  width=110, on_click=lambda e: change_sort("Current Price")),
                        ft.TextButton(get_label("Difference"),     width=110, on_click=lambda e: change_sort("Difference")),
                        ft.TextButton(get_label("P/L(%)"),         width=100, on_click=lambda e: change_sort("P/L(%)")),
                        ft.TextButton(get_label("P/L"),            width=100, on_click=lambda e: change_sort("P/L")),
                    ]),
                    ft.Divider(height=1),
                    ft.Column(ref=table_ref, spacing=4),
                ]),
                padding=12,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
            ),
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        )

    def build_search_tab():
        return ft.Column([
            ft.Text("Stock Chart", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Search any ticker to view its price history.",
                    size=13, color=ft.Colors.GREY_600),
            ft.Row([
                ft.TextField(
                    ref=stock_symbol,
                    label="Stock Symbol",
                    hint_text="AAPL, GOOGL, MSFT...",
                    expand=True,
                    on_submit=fetch_stock_data,
                ),
                ft.Dropdown(
                    ref=time_range_dd,
                    label="Range",
                    width=130,
                    value="30 days",
                    options=[ft.dropdown.Option(k) for k in RANGE_MAP],
                ),
                ft.FilledButton("Search", icon=ft.Icons.SEARCH, on_click=fetch_stock_data),
            ], spacing=8),
            ft.Container(ref=error_messages, content=ft.Text("", color=ft.Colors.RED, size=13), visible=False),
            ft.Container(ref=price_info, padding=ft.Padding.symmetric(vertical=6), visible=False),
            ft.Container(ref=chart_container, padding=0, visible=False),
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        )

    tab_content = ft.Ref[ft.Container]()
    active_tab  = {"index": 0}
    tab_buttons = []

    def make_tab_btn(label, index):
        def on_click(e):
            active_tab["index"] = index
            tab_content.current.content = (
                build_portfolio_tab() if index == 0 else build_search_tab()
            )
            if index == 0:
                if perf_chart_ref.current and portfolio_history:
                    perf_chart_ref.current.content = build_perf_chart()
                if alloc_chart_ref.current and not df_display["Current Price"].isna().any():
                    alloc_chart_ref.current.content = build_alloc_chart(df_display)

            for i, btn in enumerate(tab_buttons):
                btn.style = ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_700 if i == index else ft.Colors.TRANSPARENT,
                    color=ft.Colors.WHITE     if i == index else ft.Colors.BLUE_700,
                    side=ft.BorderSide(1, ft.Colors.BLUE_700),
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                )
            page.update()

        btn = ft.FilledButton(
            label,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700 if index == 0 else ft.Colors.TRANSPARENT,
                color=ft.Colors.WHITE     if index == 0 else ft.Colors.BLUE_700,
                side=ft.BorderSide(1, ft.Colors.BLUE_700),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=20, vertical=10),
            ),
            on_click=on_click,
        )
        tab_buttons.append(btn)
        return btn

    page.add(
        ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Text("Gotcha Portfolio", size=22, weight=ft.FontWeight.BOLD),
                    ft.Row([make_tab_btn(t, i) for i, t in enumerate(["Portfolio", "Search"])],spacing=8),
                    theme_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding.only(left=20, right=20, top=12, bottom=12),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
            ),
            ft.Container(
                ref=tab_content,
                content=build_portfolio_tab(),
                padding=ft.Padding.only(left=20, right=20, top=12, bottom=12),
                expand=True,
            ),
        ], expand=True, spacing=0)
    )

    asyncio.create_task(fetch_latest_price())
    asyncio.create_task(fetch_portfolio_history())

    while True:
        await asyncio.sleep(1)

        now = datetime.now()
        if clock_ref.current:
            clock_ref.current.value = (
                f"Portfolio Performance - {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        if history_ready.is_set() and perf_chart_ref.current:
            perf_chart_ref.current.content = build_perf_chart()
            history_ready.clear()

        if fetch_complete.is_set():
            df_display["Current Price"] = latest_prices.copy()
            df_display["Difference"]    = df_display["Current Price"] - df_display["Purchase Price"]
            df_display["P/L(%)"]        = df_display["Difference"] / df_display["Purchase Price"] * 100
            df_display["P/L"]           = df_display["Difference"] * df_display["Number of Shares"]

            if table_ref.current:
                table_ref.current.controls = build_table(sort_df(df_display))

            if df_display["Current Price"].notna().all() and totals_ref.current:
                total_cost = (df_display["Purchase Price"] * df_display["Number of Shares"]).sum()
                total_val  = (df_display["Current Price"]  * df_display["Number of Shares"]).sum()
                total_pl   = df_display["P/L"].sum()
                total_pct  = (total_val - total_cost) / total_cost * 100

                totals_ref.current.content = ft.Row([
                    build_stat_card("Investment", fmt_money(total_cost), get_theme()["accent"]),
                    build_stat_card("Value",      fmt_money(total_val),  get_theme()["purple"]),
                    build_stat_card("Change",     fmt_pct(total_pct),
                                    get_theme()["green"] if total_pct >= 0 else get_theme()["red"]),
                    build_stat_card("P/L",        fmt_money(total_pl),
                                    get_theme()["green"] if total_pl   >= 0 else get_theme()["red"]),
                ], spacing=10)

                if alloc_chart_ref.current:
                    alloc_chart_ref.current.content = build_alloc_chart(df_display)

            fetch_complete.clear()

        page.update()

if __name__ == "__main__":
    ft.run(main)