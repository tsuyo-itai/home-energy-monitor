import flet as ft
import logging
import asyncio
from echonet import EchonetClient
import os

# Configuration
MOCK_MODE = os.getenv("ECHONET_MOCK") == "1"

# Initialize Backend (Global Singleton)
client = EchonetClient(mock=MOCK_MODE)
client.start()

# 充電推奨しきい値
CHARGE_HIGH_RECOMMENDATION_THRESHOLD = 2500
CHARGE_NORMAL_RECOMMENDATION_THRESHOLD = 1500
CHARGE_LOW_RECOMMENDATION_THRESHOLD = 750


def main(page: ft.Page):
    page.title = "ホームエネルギーモニター"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#1a1a1a"

    # ---------------- UI ----------------

    header_text = ft.Text(
        "ホームエネルギーモニター",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE_70,
    )

    status_indicator = ft.Container(
        width=10, height=10, border_radius=5, bgcolor=ft.Colors.GREEN
    )

    status_text = ft.Text("システム稼働中", size=12, color=ft.Colors.GREEN)

    header = ft.Container(
        content=ft.Row(
            [
                header_text,
                ft.Row([status_indicator, status_text], spacing=5),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=20,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )

    net_power_val = ft.Text("計測中...", size=48, weight=ft.FontWeight.BOLD)
    net_power_label = ft.Text("電力収支", size=14, color=ft.Colors.WHITE_54)

    net_card_bg = ft.Container(
        content=ft.Column(
            [net_power_label, net_power_val],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=300,
        height=200,
        border_radius=20,
        padding=40,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLACK],
        ),
    )

    cons_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD)
    gen_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD)

    details_row = ft.Row(
        [
            ft.Column([ft.Text("消費電力"), cons_val]),
            ft.Column([ft.Text("太陽光発電"), gen_val]),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=40,
    )

    body = ft.Column(
        [
            net_card_bg,
            ft.Container(height=20),
            details_row,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    page.add(header, body)

    # ---------------- async UI updater ----------------

    async def update_data():
        while True:
            data = client.get_data()
            if data["last_updated"] == 0:
                await asyncio.sleep(0.5)
                continue

            c = data["consumption"]
            g = data["generation"]

            gen_val.value = f"{g} W"

            if c is not None:
                net = -1 * c
                cons = max(g + c, 0)
                cons_val.value = f"{cons} W"
            else:
                net = 0
                cons_val.value = "-- W"

            prefix = "+" if net > 0 else ""
            net_power_val.value = f"{prefix}{net} W"

            # 状態表示
            if net > 0:
                status_text.value = "売電中"
                status_text.color = ft.Colors.GREEN_400
                status_indicator.bgcolor = ft.Colors.GREEN_400
                net_card_bg.gradient.colors = [ft.Colors.GREEN_600, ft.Colors.BLACK]
            else:
                status_text.value = "買電中"
                status_text.color = ft.Colors.ORANGE_400
                status_indicator.bgcolor = ft.Colors.ORANGE_400
                net_card_bg.gradient.colors = [ft.Colors.RED_400, ft.Colors.BLACK]

            page.update()
            await asyncio.sleep(1)

    # ★ ここが重要：Fletイベントループ上で実行
    page.run_task(update_data)

    def on_disconnect(e):
        logging.info("Session disconnected.")

    page.on_disconnect = on_disconnect


if __name__ == "__main__":
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=8550,
    )