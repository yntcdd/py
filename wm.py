# python -m pip install pywin32 pynput
# powershell Get-Clipboard > w.py

import win32gui
import time
from pynput import mouse
from datetime import datetime

def enum_window_callback(hwnd, results):
    title = win32gui.GetWindowText(hwnd)
    if win32gui.IsWindowVisible(hwnd) and title:
        results.append(title)

def list_open_windows():
    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)
    return windows

def get_foreground_window_title():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        return win32gui.GetWindowText(hwnd)
    return None

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Mouse click listener
def on_click(x, y, button, pressed):
    if pressed:
        print(f"[{timestamp()}] Mouse clicked: {button} at ({x}, {y})")

if __name__ == "__main__":
    # Print all currently open windows
    print("Open windows:")
    for title in list_open_windows():
        print(" -", title)

    print("\nTracking focus changes and mouse clicks (Ctrl+C to stop)...\n")

    # Start mouse listener in background
    # listener = mouse.Listener(on_click=on_click)
    # listener.start()

    last_title = None
    try:
        while True:
            current_title = get_foreground_window_title()
            if current_title and current_title != last_title:
                print(f"[{timestamp()}] Focused window: {current_title}")
                last_title = current_title
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped tracking.")
        # listener.stop()
