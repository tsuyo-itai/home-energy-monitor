import flet as ft
import time
import threading
from echonet import EchonetClient

import os

# Configuration
# Set to True if testing without real Echonet devices
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
    page.window_width = 800
    page.window_height = 600
    page.bgcolor = "#1a1a1a" # Fallback setup



    # --- UI Components ---

    # Header
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
                ft.Row([status_indicator, status_text], spacing=5)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.Padding(left=30, right=30, top=20, bottom=20),
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )

    # Main Power Gauge (Net Power)
    # Visualizing Net Power:
    # If Gen > Cons: Green Gradient (Exporting)
    # If Cons > Gen: Orange/Red Gradient (Importing)
    
    net_power_val = ft.Text("計測中...", size=48, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    net_power_label = ft.Text("電力収支", size=14, color=ft.Colors.WHITE_54)
    
    net_card_bg = ft.Container(
        content=ft.Column(
            [
                net_power_label,
                net_power_val,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[ft.Colors.BLUE_GREY_900, ft.Colors.BLACK],
        ),
        border_radius=20,
        padding=40,
        width=300,
        height=200,
        shadow=ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 10),
        )
    )

    # Recommendation Banner
    ev_icon = ft.Icon(ft.Icons.EV_STATION, size=30, color=ft.Colors.WHITE)
    rec_text = ft.Text("解析中...", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE)
    
    recommendation_card = ft.Container(
        content=ft.Row(
            [ev_icon, rec_text],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        ),
        bgcolor=ft.Colors.GREY_800,
        border_radius=15,
        padding=15,
        margin=ft.Margin(top=20),
        width=300
    )


    # Details Row (Consumption vs Generation)
    def create_detail_card(title, value_ref, icon, color):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=30),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.1, color),
                        border_radius=10,
                    ),
                    ft.Column(
                        [
                            ft.Text(title, size=12, color=ft.Colors.WHITE_54),
                            value_ref
                        ],
                        spacing=2
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.GREY_900,
            border_radius=15,
            padding=20,
            width=220,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
        )

    cons_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    gen_val = ft.Text("-- W", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    details_row = ft.Row(
        [
            create_detail_card("消費電力", cons_val, ft.Icons.HOME, ft.Colors.ORANGE_400),
            create_detail_card("太陽光発電", gen_val, ft.Icons.WB_SUNNY, ft.Colors.YELLOW_400),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
        wrap=True
    )

    # Main Layout Assembly
    body = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=15), # Spacer
                net_card_bg,
                recommendation_card,
                ft.Container(height=15), # Spacer
                details_row,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        expand=True,
        alignment=ft.Alignment(0, 0)
    )

    page.add(header, body)

    # --- Data Update Loop ---
    def update_data():
        while True:
            data = client.get_data()
            if data["last_updated"] == 0:
                time.sleep(0.5)
                continue
            
            c = data["consumption"]
            g = data["generation"]
            
            # Update Values
            gen_val.value = f"{g} W"
            
            # Smart Meter C: + = Buy (Import), - = Sell (Export)
            # Net for UI: + = Profit (Sell), - = Cost (Buy)
            # So Net = -1 * C
            if c is not None:
                net = -1 * c
                # Calculate Consumption: Gen + Grid(Import) - Grid(Export)
                # c is (+Import / -Export).
                # Consumption = Gen + c
                calc_cons = g + c
                if calc_cons < 0: calc_cons = 0 # Safety clamp
                cons_val.value = f"{calc_cons} W"
            else:
                net = 0
                cons_val.value = "-- W"
            prefix = "+" if net > 0 else ""
            net_power_val.value = f"{prefix}{net} W"
            
            # Update UI Colors/Styles based on state
            if net > 0:
                # Excess Power (Green theme)
                status_text.value = "売電中"
                status_text.color = ft.Colors.GREEN_400
                status_indicator.bgcolor = ft.Colors.GREEN_400
                
                if net > CHARGE_HIGH_RECOMMENDATION_THRESHOLD:
                    # High Recommendation
                    net_card_bg.gradient.colors = [ft.Colors.GREEN_700, ft.Colors.BLACK]
                    
                    rec_text.value = "EV充電: やった方が良い"
                    rec_text.color = ft.Colors.GREEN_100
                    recommendation_card.bgcolor = ft.Colors.GREEN_700
                    ev_icon.color = ft.Colors.GREEN_100
                elif net > CHARGE_NORMAL_RECOMMENDATION_THRESHOLD:
                    # Normal Recommendation
                    net_card_bg.gradient.colors = [ft.Colors.GREEN_400, ft.Colors.BLACK]
                    
                    rec_text.value = "EV充電: まぁまぁ"
                    rec_text.color = ft.Colors.GREEN_50
                    recommendation_card.bgcolor = ft.Colors.GREEN_400
                    ev_icon.color = ft.Colors.GREEN_50
                elif net > CHARGE_LOW_RECOMMENDATION_THRESHOLD:
                    # Low Recommendation
                    net_card_bg.gradient.colors = [ft.Colors.GREEN_300, ft.Colors.BLACK]
                    
                    rec_text.value = "EV充電: あんまりよくない"
                    rec_text.color = ft.Colors.ORANGE_50
                    recommendation_card.bgcolor = ft.Colors.ORANGE_600
                    ev_icon.color = ft.Colors.ORANGE_50
                else:
                    # No Recommendation
                    net_card_bg.gradient.colors = [ft.Colors.DEEP_ORANGE_400, ft.Colors.BLACK]
                    
                    rec_text.value = "EV充電: しないほうが良い"
                    rec_text.color = ft.Colors.DEEP_ORANGE_100
                    recommendation_card.bgcolor = ft.Colors.DEEP_ORANGE_700
                    ev_icon.color = ft.Colors.DEEP_ORANGE_100
            else:
                # Deficit (Red/Orange theme)
                net_card_bg.gradient.colors = [ft.Colors.RED_400, ft.Colors.BLACK]
                status_text.value = "買電中"
                status_text.color = ft.Colors.ORANGE_400
                status_indicator.bgcolor = ft.Colors.ORANGE_400
                
                # Recommendation
                rec_text.value = "EV充電: 夜間に充電"
                rec_text.color = ft.Colors.WHITE_70
                recommendation_card.bgcolor = ft.Colors.GREY_800
                ev_icon.color = ft.Colors.WHITE_70

            page.update()
            time.sleep(1) # UI Refresh rate (separate from polling)

    # Start UI Thread
    ui_thread = threading.Thread(target=update_data, daemon=True)
    ui_thread.start()

    # Cleanup on close
    def on_disconnect(e):
        print("Session disconnected.")

    page.on_disconnect = on_disconnect

if __name__ == "__main__":
    ft.app(main)
