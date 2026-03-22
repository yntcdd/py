import math
import time
import threading
from datetime import datetime

import flet as ft
import flet.canvas as cv


def main(page: ft.Page):
    page.title = "Clock"
    page.window_width = 420
    page.window_height = 500
    page.window_resizable = False
    page.bgcolor = "#0D0D1A"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ── Geometry ─────────────────────────────────────────────────────────────
    SIZE = 280
    CX = SIZE / 2
    CY = SIZE / 2
    R = SIZE / 2 - 10

    def hand_end(angle_deg, length):
        rad = math.radians(angle_deg - 90)
        return CX + length * math.cos(rad), CY + length * math.sin(rad)

    # ── Shape builders ────────────────────────────────────────────────────────
    def build_shapes(now: datetime):
        shapes = []

        # Background circle
        shapes.append(cv.Circle(CX, CY, R,
            ft.Paint(color="#1E1E3A", style=ft.PaintingStyle.FILL)))
        shapes.append(cv.Circle(CX, CY, R,
            ft.Paint(color="#6C63FF", stroke_width=2, style=ft.PaintingStyle.STROKE)))

        # Hour tick marks
        for i in range(12):
            angle = math.radians(i * 30 - 90)
            x1 = CX + (R - 4) * math.cos(angle)
            y1 = CY + (R - 4) * math.sin(angle)
            x2 = CX + (R - 18) * math.cos(angle)
            y2 = CY + (R - 18) * math.sin(angle)
            shapes.append(cv.Line(x1, y1, x2, y2,
                ft.Paint(color="#6C63FF", stroke_width=2.5)))

        # Minute tick marks
        for i in range(60):
            if i % 5 == 0:
                continue
            angle = math.radians(i * 6 - 90)
            x1 = CX + (R - 4) * math.cos(angle)
            y1 = CY + (R - 4) * math.sin(angle)
            x2 = CX + (R - 10) * math.cos(angle)
            y2 = CY + (R - 10) * math.sin(angle)
            shapes.append(cv.Line(x1, y1, x2, y2,
                ft.Paint(color="#3A3A60", stroke_width=1)))

        # Hour hand
        h_angle = (now.hour % 12) * 30 + now.minute * 0.5
        hx, hy = hand_end(h_angle, R * 0.50)
        shapes.append(cv.Line(CX, CY, hx, hy,
            ft.Paint(color="#E0E0FF", stroke_width=6,
                     stroke_cap=ft.StrokeCap.ROUND)))

        # Minute hand
        m_angle = now.minute * 6 + now.second * 0.1
        mx, my = hand_end(m_angle, R * 0.72)
        shapes.append(cv.Line(CX, CY, mx, my,
            ft.Paint(color="#A0A0FF", stroke_width=3,
                     stroke_cap=ft.StrokeCap.ROUND)))

        # Second hand
        s_angle = now.second * 6
        sx, sy = hand_end(s_angle, R * 0.78)
        shapes.append(cv.Line(CX, CY, sx, sy,
            ft.Paint(color="#FF6C6C", stroke_width=1.5,
                     stroke_cap=ft.StrokeCap.ROUND)))

        # Centre dots
        shapes.append(cv.Circle(CX, CY, 6,
            ft.Paint(color="#6C63FF", style=ft.PaintingStyle.FILL)))
        shapes.append(cv.Circle(CX, CY, 3,
            ft.Paint(color="#FF6C6C", style=ft.PaintingStyle.FILL)))

        return shapes

    # ── Controls ──────────────────────────────────────────────────────────────
    clock_canvas = cv.Canvas(
        shapes=build_shapes(datetime.now()),
        width=SIZE,
        height=SIZE,
    )

    time_text = ft.Text(
        "",
        size=44,
        weight=ft.FontWeight.W_300,
        color="#E0E0FF",
        font_family="monospace",
    )
    date_text = ft.Text(
        "",
        size=13,
        weight=ft.FontWeight.W_400,
        color="#6C63FF",
        style=ft.TextStyle(letter_spacing=2),
    )

    def refresh(now: datetime):
        clock_canvas.shapes = build_shapes(now)
        time_text.value = now.strftime("%H:%M:%S")
        date_text.value = now.strftime("%A, %B %d %Y").lstrip("0").upper()

    # ── Tick thread ───────────────────────────────────────────────────────────
    running = True

    def tick():
        while running:
            refresh(datetime.now())
            try:
                page.update()
            except Exception:
                break
            time.sleep(1)

    def on_close(e):
        nonlocal running
        running = False

    page.on_close = on_close

    thread = threading.Thread(target=tick, daemon=True)
    thread.start()

    # ── Layout ────────────────────────────────────────────────────────────────
    refresh(datetime.now())

    page.add(
        ft.Column(
            [
                clock_canvas,
                ft.Container(height=16),
                time_text,
                ft.Container(height=4),
                date_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
    )


ft.app(target=main)