# python -m pip install pywin32 pynput
# powershell Get-Clipboard > wmf.py
# export PATH=$PATH:C:/nvm4w/nodejs
# nodemon --exec python wmf.py
import win32gui
import time
from pynput import mouse
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
# formatter = logging.Formatter("%(asctime)s - %(message)s", style="{", datefmt="%Y-%m-%d %H:%M:%S")

# file_handler = logging.FileHandler("wmf_log.txt", mode="a", encoding="utf-8")
file_handler = TimedRotatingFileHandler("wmflg", when="midnight", interval=1, backupCount=7, encoding="utf-8")
# file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
# Configure logging: write to file and also show in console
# logging.basicConfig(
#     filename="wmf_log.txt",       # log file name
#     level=logging.INFO,
#     format="%(asctime)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     encoding="utf-8"
# )

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
        msg = f"Mouse clicked: {button} at ({x}, {y})"
        print(f"[{timestamp()}] {msg}")
        logging.info(msg)

if __name__ == "__main__":
    # Print all currently open windows
    logger.info("Open windows:")
    for title in list_open_windows():
        # print(" -", title)
        # logging.info(title)
        logger.info(title)

    print("\nTracking focus changes and mouse clicks (Ctrl+C to stop)...\n")

    # Start mouse listener in background
    # listener = mouse.Listener(on_click=on_click)
    # listener.start()

    last_title = None
    try:
        while True:
            current_title = get_foreground_window_title()
            if current_title and current_title != last_title:
                # msg = f"Focused window: {current_title}"
                msg = current_title
                # print(f"[{timestamp()}] {msg}")
                logger.info(msg)
                last_title = current_title
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped tracking.")
        # listener.stop()
