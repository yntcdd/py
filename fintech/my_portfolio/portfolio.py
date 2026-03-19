import pandas as pd
import yfinance as yf
import time
import threading
import sys
from datetime import datetime
import flet as ft

def main(page: ft.Page):
    def pick_folder(e):
        print("Folder selected")

    page.add(
        ft.ElevatedButton("Select Folder", on_click=pick_folder)
    )

ft.app(target=main)