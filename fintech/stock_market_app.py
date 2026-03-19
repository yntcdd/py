# Flet Stock App Live Data & Charts

import flet as ft
import flet.charts as fch
import requests
from config import API_KEY

# Main Flet Interface -> function based

def main(page: ft.Page):
    # App settings
    page.title = "Gotcha Stock!"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 1000
    page.window_height = 700
    
    # Read the Flet Documentation, it's really good!
    
    # State Variables - Widgets in our App
    stock_symbol = ft.Ref[ft.TextField]() # GOOGL APPL
    chart_container = ft.Ref[ft.Container]()
    price_info = ft.Ref[ft.Container]()
    price_text_below = ft.Ref[ft.Container]()
    error_messages = ft.Ref[ft.Container]()
    time_range_dropdown = ft.Ref[ft.Dropdown]()
    
    # Time range for the stock
    def get_days_for_range(range_name):
        ranges = {
            "1 week": 7,
            "2 weeks": 14,
            "30 days": 30,
            "90 days": 90,
            "1 year": 365,
            "5 years": 1825
        }
        return ranges.get(range_name, 30)
    
    def get_range_label(range_name):
        return range_name

    # Fetch the Stock with our API
    def fetch_stock_data(e):
        symbol = stock_symbol.current.value.upper().strip()
        time_range = time_range_dropdown.current.value or "30 days"
        days = get_days_for_range(time_range) # 365
    
        # Mini Error handle
        if not symbol:
            error_messages.current.content = ft.Text("Please enter stock symbol.", color = ft.Colors.RED, size = 14)
            error_messages.current.visible = True
            price_info.current.visible = False
            price_text_below.current.visible = False
            chart_container.current.visible = False
            page.update()
            return
        
        error_messages.current.visible = False
        error_messages.current.content = ft.Text("", color = ft.Colors.RED, size = 14)
        
        # Load the Stock.. waiting
        loading_Text = ft.Text("Loading Stock Data...", size = 16, color = ft.Colors.BLUE, italic = True)
        chart_container.current.content = loading_Text
        price_info.current.visible = False
        price_text_below.current.visible = False
        chart_container.current.visible = True
        page.update()
        
        # Fetch the API data
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            time_series = data["Time Series (Daily)"]
            
            dates = sorted(time_series.keys(), reverse=True)[:days]
            dates.reverse()
            
            # Prep the charts
            opens, highs, lows, closes = [], [], [], []
            for date in dates:
                day_date = time_series[date]
                open_price = float(day_date["1. open"])
                high_price = float(day_date["2. high"])
                low_price = float(day_date["3. low"])
                close_price = float(day_date["4. close"])
                
                opens.append(open_price)
                highs.append(high_price)
                lows.append(low_price)
                closes.append(close_price)
            
            latest_date = sorted(time_series.keys(), reverse=True)[0]
            latest_data = time_series[latest_date]
            
            # Time to make some charts in Flet!
            # Update price info
            price_info.current.content = ft.Column([
                ft.Text(f"Stock: {symbol}", size = 24, weight = ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                ft.Text(f"Date: {latest_date}", size = 14, weight = ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
                ft.Divider(height = 1),
                
                ft.Row([
                    ft.Container(
                        content = ft.Column([
                            ft.Text(f"Open", size = 12, color = ft.Colors.GREY_600),
                            ft.Text(f"${float(latest_data['1. open']):.2f}", size = 20, weight = ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ], spacing = 5),
                        padding = 15,
                        bgcolor = ft.Colors.BLUE_50,
                        border_radius = 10,
                        expand = True
                    ),
                    ft.Container(
                        content = ft.Column([
                            ft.Text(f"High", size = 12, color = ft.Colors.GREY_600),
                            ft.Text(f"${float(latest_data['2. high']):.2f}", size = 20, weight = ft.FontWeight.BOLD, color=ft.Colors.GREEN_900),
                        ], spacing = 5),
                        padding = 15,
                        bgcolor = ft.Colors.GREEN_50,
                        border_radius = 10,
                        expand = True
                    ),
                    ft.Container(
                        content = ft.Column([
                            ft.Text(f"Low", size = 12, color = ft.Colors.GREY_600),
                            ft.Text(f"${float(latest_data['3. low']):.2f}", size = 20, weight = ft.FontWeight.BOLD, color=ft.Colors.RED_900),
                        ], spacing = 5),
                        padding = 15,
                        bgcolor = ft.Colors.RED_50,
                        border_radius = 10,
                        expand = True
                    ),
                    ft.Container(
                        content = ft.Column([
                            ft.Text(f"Close", size = 12, color = ft.Colors.GREY_600),
                            ft.Text(f"${float(latest_data['4. close']):.2f}", size = 20, weight = ft.FontWeight.BOLD, color=ft.Colors.PURPLE_900),
                        ], spacing = 5),
                        padding = 15,
                        bgcolor = ft.Colors.PURPLE_50,
                        border_radius = 10,
                        expand = True
                    ),
                ], spacing = 10)
            ])
            price_info.current.visible = True
            # Containers -> Columns and rows
            
            # Make the Charts
            chart = fch.LineChart(
                data_series = [
                    ft.LineChartData(
                        data_points = [
                            fch.LineChartDataPoint(i, closes[i])
                            for i in range(len(closes))
                        ],
                        stroke_width = 3,
                        color = ft.Colors.ORANGE,
                        below_line_bgcolor = ft.Colors.ORANGE_100,
                    ),
                ],
                border = ft.Border(
                    bottom = ft.BorderSide(4, ft.Colors.with_opacity(ft.Colors.ON_SURFACE, 0.5)),
                    left = ft.BorderSide(4, ft.Colors.with_opacity(ft.Colors.ON_SURFACE, 0.5)),
                    top = ft.BorderSide(4, ft.Colors.with_opacity(ft.Colors.ON_SURFACE, 0.5)),
                    right = ft.BorderSide(4, ft.Colors.with_opacity(ft.Colors.ON_SURFACE, 0.5)),
                ),
                left_axis = fch.ChartAxis(
                    labels_size = 50,
                ),
                bottom_axis = fch.ChartAxis(
                    labels_size = 40,
                    labels_interval = max(1, len(closes) // 10),
                ),
                tooltip = ft.Colors.with_opacity(ft.Colors.BLUE_GREY, 0.8),
                min_y = min(closes) * 0.95,
                max_y = max(closes) * 1.05,
                min_x = 0,
                max_x = len(closes) - 1,
                expand = True
            )
            
            chart_container.current.content = ft.Container(
                content = ft.Column([
                    ft.Text(f"Closing Price - {get_range_label(time_range)} ({symbol})", size = 18, weight = ft.FontWeight.BOLD),
                    chart
                ], spacing = 10),
                padding = 20,
                border = ft.border.all(2, ft.Colors.GREY_300),
                border_radius = 10
            )
            chart_container.current.visible = True
            
            # Add Price Text below the chart
            price_text_below.current.content = ft.Text(
                f"Open: ${float(latest_data['1. open']):.2f} |"
                f"High: ${float(latest_data['2. high']):.2f} | "
                f"Low: ${float(latest_data['3. low']):.2f} | "
                f"Close: ${float(latest_data['4. close']):.2f} | ",
                size = 16,
                weight = ft.FontWeight.BOLD,
                text_align = ft.TextAlign.CENTER,
            )
            price_text_below.current.visible = True
        
        except Exception as e:
            loading_Text = ft.Text(f"Error fetching data...{e}", size = 16, color = ft.Colors.RED, italic = True)
            chart_container.current.content = loading_Text
            price_info.current.visible = False
            price_text_below.current.visible = False
            chart_container.current.visible = True
            
        page.update()
        
    # UI Layout
    page.add(
        ft.Column([
            ft.Container(
                content = ft.Column([
                    ft.Text("Gotcha Stock App on Code with Josh", size = 30, weight = ft.FontWeight.BOLD, color = ft.Colors.BLUE_800),
                    ft.Text("Enter a stock symbol to view the chart.", size = 14, color = ft.Colors.GREY_600),
                ], spacing = 5, horizontal_alignment = ft.CrossAxisAlignment.CENTER),
                padding = ft.padding.only(bottom = 20),
                alignment = ft.Alignment(0, 0)
            ),
            # Search bar and date picker
            ft.Container(
                content = ft.Row([
                    ft.TextField(
                        ref = stock_symbol, 
                        label = "Stock Symbol (e.g. AAPL)", 
                        hint_text = "AAPL, GOOGL, MSFT",
                        width = 300,
                        autofocus = True,
                        on_submit = fetch_stock_data,
                    ),
                    ft.Dropdown(
                        ref = time_range_dropdown,
                        label = "Time Range",
                        width = 150,
                        options = [
                            ft.dropdown.Option("1 week"),
                            ft.dropdown.Option("2 weeks"),
                            ft.dropdown.Option("30 days"),
                            ft.dropdown.Option("90 days"),
                            ft.dropdown.Option("1 year"),
                            ft.dropdown.Option("5 years"),
                        ],
                        value = "30 days"
                    ),
                    ft.ElevatedButton(
                        "Get Stock Data",
                        icon = ft.Icons.SEARCH,
                        on_click = fetch_stock_data,
                        style = ft.ButtonStyle(
                            color = ft.Colors.WHITE,
                            bgcolor = ft.Colors.BLUE_700,
                        ),
                    ),
                ], spacing = 10, alignment = ft.MainAxisAlignment.CENTER
                ),
                alignment = ft.Alignment(0, 0)
            ),
            ft.Container(
                ref = error_messages,
                content = ft.Text("", color = ft.Colors.RED, size = 14),
                padding = 10,
                visible = False
            ),
            ft.Container(
                ref = price_info,
                padding = 10,
                visible = False
            ),
            ft.Container(
                ref = chart_container,
                padding = 10,
                visible = False
            ),
            ft.Container(
                ref = price_text_below,
                padding = 10,
                visible = False
            )
        ], spacing = 15)
    )
    
if __name__ == "__main__":
    ft.app(target=main)