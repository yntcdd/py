# python -m pip install pywin32 pynput
# powershell Get-Clipboard > w.py
import win32gui
import time

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

if __name__ == "__main__":
    # Print all currently open windows
    print("Opened windows:")
    for title in list_open_windows():
        print(" -", title)

    print("\nTracking focus changes (Ctrl+C to stop)...\n")

    last_title = None
    try:
        while True:
            current_title = get_foreground_window_title()
            if current_title and current_title != last_title:
                print(f"->: {current_title}")
                last_title = current_title
            time.sleep(0.5)  # check twice per second
    except KeyboardInterrupt:
        print("\nStopped tracking.")

