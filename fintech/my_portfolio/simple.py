import flet as ft
import threading
import time

def main(page: ft.Page):
    # Page configuration
    page.title = "⏱️ Auto Counter"
    page.window_width = 400
    page.window_height = 300
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_50
    
    # Counter state
    counter_value = 0
    running = True
    
    # UI Components
    counter_text = ft.Text(
        "0",
        size=80,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.INDIGO_600,
        text_align=ft.TextAlign.CENTER
    )
    
    status_text = ft.Text(
        "Counter is running...",
        size=14,
        color=ft.Colors.GREEN_600,
        italic=True
    )
    
    # Control buttons
    def toggle_counter(e):
        nonlocal running
        running = not running
        if running:
            toggle_btn.text = "⏸ Pause"
            toggle_btn.icon = ft.Icons.PAUSE
            status_text.value = "Counter is running..."
            status_text.color = ft.Colors.GREEN_600
        else:
            toggle_btn.text = "▶ Resume"
            toggle_btn.icon = ft.Icons.PLAY_ARROW
            status_text.value = "Counter paused"
            status_text.color = ft.Colors.ORANGE_600
        page.update()
    
    def reset_counter(e):
        nonlocal counter_value
        counter_value = 0
        counter_text.value = "0"
        page.update()
    
    toggle_btn = ft.ElevatedButton(
        "⏸ Pause",
        icon=ft.Icons.PAUSE,
        on_click=toggle_counter,
        width=140
    )
    
    reset_btn = ft.ElevatedButton(
        "🔄 Reset",
        icon=ft.Icons.REFRESH,
        on_click=reset_counter,
        width=140,
        bgcolor=ft.Colors.RED_100,
        color=ft.Colors.RED_700
    )
    
    # SAFE update function - runs on main UI thread via page.run()
    def update_ui():
        counter_text.value = str(counter_value)
        page.update()
    
    # Counter update thread - uses page.run() to safely update UI
    def counter_thread():
        nonlocal counter_value
        while True:
            time.sleep(1)
            if running:
                counter_value += 1
                # Schedule UI update on main thread
                page.run(update_ui)
    
    # Start the counter thread
    threading.Thread(target=counter_thread, daemon=True).start()
    
    # Layout
    page.add(
        ft.Column(
            [
                ft.Text("Auto Counter", size=28, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_800),
                ft.Container(height=30),
                counter_text,
                ft.Container(height=10),
                status_text,
                ft.Container(height=30),
                ft.Row(
                    [toggle_btn, reset_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )
    )

ft.app(target=main)
