import math
import asyncio
from datetime import datetime

import flet as ft
import flet.canvas as cv


async def main(page: ft.Page):
    page.title = "Clock"
    page.window.width = 420
    page.window.height = 500
    page.window.resizable = False
    page.bgcolor = "#0D0D1A"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # ── Geometry ──────────────────────────────────────────────────────────────
    SIZE = 280
    CX = SIZE / 2
    CY = SIZE / 2
    R = SIZE / 2 - 10

    def hand_end(angle_deg, length):
        rad = math.radians(angle_deg - 90)
        return CX + length * math.cos(rad), CY + length * math.sin(rad)

    # ── Shape builders ─────────────────────────────────────────────────────────
    def build_shapes(now: datetime):
        shapes = []

        shapes.append(cv.Circle(
            x=CX, y=CY, radius=R,
            paint=ft.Paint(color="#1E1E3A", style=ft.PaintingStyle.FILL),
        ))
        shapes.append(cv.Circle(
            x=CX, y=CY, radius=R,
            paint=ft.Paint(color="#6C63FF", stroke_width=2, style=ft.PaintingStyle.STROKE),
        ))

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            shapes.append(cv.Line(
                x1=CX + (R - 4)  * math.cos(angle),
                y1=CY + (R - 4)  * math.sin(angle),
                x2=CX + (R - 18) * math.cos(angle),
                y2=CY + (R - 18) * math.sin(angle),
                paint=ft.Paint(color="#6C63FF", stroke_width=2.5),
            ))

        for i in range(60):
            if i % 5 == 0:
                continue
            angle = math.radians(i * 6 - 90)
            shapes.append(cv.Line(
                x1=CX + (R - 4)  * math.cos(angle),
                y1=CY + (R - 4)  * math.sin(angle),
                x2=CX + (R - 10) * math.cos(angle),
                y2=CY + (R - 10) * math.sin(angle),
                paint=ft.Paint(color="#3A3A60", stroke_width=1),
            ))

        h_angle = (now.hour % 12) * 30 + now.minute * 0.5
        hx, hy = hand_end(h_angle, R * 0.50)
        shapes.append(cv.Line(
            x1=CX, y1=CY, x2=hx, y2=hy,
            paint=ft.Paint(color="#E0E0FF", stroke_width=6,
                           stroke_cap=ft.StrokeCap.ROUND),
        ))

        m_angle = now.minute * 6 + now.second * 0.1
        mx, my = hand_end(m_angle, R * 0.72)
        shapes.append(cv.Line(
            x1=CX, y1=CY, x2=mx, y2=my,
            paint=ft.Paint(color="#A0A0FF", stroke_width=3,
                           stroke_cap=ft.StrokeCap.ROUND),
        ))

        s_angle = now.second * 6
        sx, sy = hand_end(s_angle, R * 0.78)
        shapes.append(cv.Line(
            x1=CX, y1=CY, x2=sx, y2=sy,
            paint=ft.Paint(color="#FF6C6C", stroke_width=1.5,
                           stroke_cap=ft.StrokeCap.ROUND),
        ))

        shapes.append(cv.Circle(
            x=CX, y=CY, radius=6,
            paint=ft.Paint(color="#6C63FF", style=ft.PaintingStyle.FILL),
        ))
        shapes.append(cv.Circle(
            x=CX, y=CY, radius=3,
            paint=ft.Paint(color="#FF6C6C", style=ft.PaintingStyle.FILL),
        ))

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

    # ── Async tick loop ───────────────────────────────────────────────────────
    while True:
        await asyncio.sleep(1)
        refresh(datetime.now())
        page.update()


ft.run(main)