import flet as ft
import logging
import asyncio
from echonet import EchonetClient
import os
from datetime import datetime

# Configuration
MOCK_MODE = os.getenv("ECHONET_MOCK") == "1"

# Initialize Backend (Global Singleton)
client = EchonetClient(mock=MOCK_MODE)
client.start()

# EV充電推奨しきい値 (W)
CHARGE_LEVEL5_THRESHOLD = 3000  # 充電最適
CHARGE_LEVEL4_THRESHOLD = 2000  # 充電良好
CHARGE_LEVEL3_THRESHOLD = 1000  # 充電可能
CHARGE_LEVEL2_THRESHOLD = 0     # 充電注意（少し買電増）
# それ以下: 充電しない方が良い


def main(page: ft.Page):
    page.title = "ホームエネルギーモニター"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = "#1a1a1a"
    page.window_width = 400
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # ---------------- UI ----------------

    status_indicator = ft.Container(
        width=10, height=10, border_radius=5, bgcolor=ft.Colors.GREEN
    )

    status_text = ft.Text("システム稼働中", size=12, color=ft.Colors.GREEN)

    last_updated_text = ft.Text("更新待ち...", size=12, color=ft.Colors.WHITE_54)

    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.ENERGY_SAVINGS_LEAF, color=ft.Colors.GREEN_400),
        leading_width=40,
        title=ft.Column([
            ft.Text("ホームエネルギーモニター", weight=ft.FontWeight.BOLD, size=16),
            last_updated_text
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
        center_title=False,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        actions=[
            ft.Container(
                content=ft.Row([status_indicator, status_text], spacing=5),
                margin=ft.Margin(0, 0, 20, 0)
            )
        ],
    )

    net_power_val = ft.Text("計測中...", size=48, weight=ft.FontWeight.BOLD)
    net_power_label = ft.Text("電力収支", size=16, color=ft.Colors.WHITE_54)

    net_card_bg = ft.Container(
        content=ft.Column(
            [
                net_power_label,
                ft.Row([
                    ft.Icon(ft.Icons.ELECTRIC_BOLT, size=32, color=ft.Colors.WHITE),
                    net_power_val
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=30,
        border_radius=20,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLACK],
        ),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        ),
        col=12,
    )

    # EV充電指標
    charge_icon = ft.Icon(ft.Icons.EV_STATION, size=28, color=ft.Colors.WHITE)
    charge_label = ft.Text("EV充電", size=12, color=ft.Colors.WHITE_54)
    charge_status_text = ft.Text("計測中...", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    charge_advice_text = ft.Text("", size=12, color=ft.Colors.WHITE70)

    charge_card = ft.Container(
        content=ft.Column([
            ft.Row([
                charge_icon,
                ft.Column([
                    charge_label,
                    charge_status_text,
                    charge_advice_text,
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.Border(
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        ),
        col=12,
    )

    cons_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD)
    gen_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD)

    cons_card = ft.Container(
        content=ft.Column([
            ft.Text("消費電力", size=14, color=ft.Colors.WHITE_54),
            ft.Row([
                ft.Icon(ft.Icons.BOLT, color=ft.Colors.ORANGE_400),
                cons_val
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.Border(
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        ),
        col=12,
    )

    gen_card = ft.Container(
        content=ft.Column([
            ft.Text("太陽光発電", size=14, color=ft.Colors.WHITE_54),
            ft.Row([
                ft.Icon(ft.Icons.SOLAR_POWER, color=ft.Colors.YELLOW_400),
                gen_val
            ], alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.Border(
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        ),
        col=12,
    )

    layout = ft.ResponsiveRow([
        net_card_bg,
        charge_card,
        cons_card,
        gen_card
    ], spacing=20)

    body = ft.Container(
        content=ft.Column([
            ft.Container(content=layout, width=400)
        ], scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20,
        expand=True,
        alignment=ft.Alignment(0, -1), # Top Center
    )

    page.add(body)

    # ---------------- async UI updater ----------------

    async def update_data():
        last_ts = 0
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

            # EV充電指標更新（5段階）
            if net >= CHARGE_LEVEL5_THRESHOLD:
                charge_status_text.value = "充電最適"
                charge_status_text.color = ft.Colors.GREEN_400
                charge_icon.color = ft.Colors.GREEN_400
                charge_advice_text.value = f"余剰 {net} W ─ フル充電OK"
                charge_card.bgcolor = ft.Colors.with_opacity(0.12, ft.Colors.GREEN)
            elif net >= CHARGE_LEVEL4_THRESHOLD:
                charge_status_text.value = "充電良好"
                charge_status_text.color = ft.Colors.LIGHT_GREEN_400
                charge_icon.color = ft.Colors.LIGHT_GREEN_400
                charge_advice_text.value = f"余剰 {net} W ─ 通常充電推奨"
                charge_card.bgcolor = ft.Colors.with_opacity(0.10, ft.Colors.LIGHT_GREEN)
            elif net >= CHARGE_LEVEL3_THRESHOLD:
                charge_status_text.value = "充電可能"
                charge_status_text.color = ft.Colors.YELLOW_400
                charge_icon.color = ft.Colors.YELLOW_400
                charge_advice_text.value = f"余剰 {net} W ─ 低速充電推奨"
                charge_card.bgcolor = ft.Colors.with_opacity(0.10, ft.Colors.YELLOW)
            elif net >= CHARGE_LEVEL2_THRESHOLD:
                charge_status_text.value = "充電注意"
                charge_status_text.color = ft.Colors.ORANGE_400
                charge_icon.color = ft.Colors.ORANGE_400
                charge_advice_text.value = f"余剰 {net} W ─ 買電が少し増えます"
                charge_card.bgcolor = ft.Colors.with_opacity(0.10, ft.Colors.ORANGE)
            else:
                charge_status_text.value = "充電しない方が良い"
                charge_status_text.color = ft.Colors.RED_400
                charge_icon.color = ft.Colors.RED_400
                charge_advice_text.value = f"買電 {-net} W ─ 充電すると更に増えます"
                charge_card.bgcolor = ft.Colors.with_opacity(0.10, ft.Colors.RED)

            # 状態表示
            if net > 0:
                # 余剰電力あり（売電中）
                status_text.value = "売電中"
                status_text.color = ft.Colors.GREEN_400
                status_indicator.bgcolor = ft.Colors.GREEN_400
                net_card_bg.gradient.colors = [ft.Colors.GREEN_600, ft.Colors.BLACK]
            else:
                # 不足電力あり（買電中）
                status_text.value = "買電中"
                status_text.color = ft.Colors.ORANGE_400
                status_indicator.bgcolor = ft.Colors.ORANGE_400
                net_card_bg.gradient.colors = [ft.Colors.RED_400, ft.Colors.BLACK]

            if data["last_updated"] != last_ts:
                last_ts = data["last_updated"]
                last_updated_text.value = f"最終更新: {datetime.fromtimestamp(last_ts).strftime('%H:%M:%S')}"

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
