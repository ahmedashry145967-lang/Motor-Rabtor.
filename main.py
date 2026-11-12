import flet as ft
import requests
import random
from bleak import BleakScanner, BleakClient

BLE_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

def main(page: ft.Page):
    page.title = "Motor Rabtor"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    haptic = ft.HapticFeedback()
    page.overlay.append(haptic)

    mode = "NONE"
    ble_client = None
    power_on = False
    obstacle = False

    ip_box = ft.TextField(label="IP الروبوت", value="192.168.4.1", width=180, height=45)
    ble_box = ft.TextField(label="اسم البلوتوث", value="MotorRabtor", width=180, height=45)
    status = ft.Text("غير متصل", color=ft.Colors.RED_ACCENT)

    def set_wifi(e):
        nonlocal mode
        mode = "WIFI"
        status.value = f"متصل Wi-Fi ({ip_box.value})"
        status.color = ft.Colors.GREEN_ACCENT
        page.update()

    async def set_ble(e):
        nonlocal mode, ble_client
        status.value = "جاري البحث..."
        page.update()
        try:
            dev = await BleakScanner.find_device_by_name(ble_box.value, timeout=4.0)
            if dev:
                ble_client = BleakClient(dev)
                await ble_client.connect()
                mode = "BLE"
                status.value = f"متصل BLE ({dev.name})"
                status.color = ft.Colors.BLUE_ACCENT
            else:
                status.value = "الجهاز غير موجود"
        except Exception:
            status.value = "فشل الاتصال"
        page.update()

    async def send(code, label):
        haptic.heavy_impact()
        if mode == "WIFI":
            try:
                requests.get(f"http://{ip_box.value}/cmd?val={code}", timeout=0.5)
            except Exception:
                pass
        elif mode == "BLE" and ble_client and ble_client.is_connected:
            try:
                await ble_client.write_gatt_char(BLE_UUID, code.encode())
            except Exception:
                pass
        page.snack_bar = ft.SnackBar(ft.Text(f"أمر: {label}"), duration=600)
        page.snack_bar.open = True
        page.update()

    def btn(text, code, icon=None, color=None, w=130):
        return ft.ElevatedButton(
            text, icon=icon, width=w, bgcolor=color,
            on_click=lambda e: page.run_task(send, code, text)
        )

    header = ft.Column([
        ft.Row([ip_box, ft.IconButton(ft.Icons.WIFI, on_click=set_wifi)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([ble_box, ft.IconButton(ft.Icons.BLUETOOTH, on_click=set_ble)], alignment=ft.MainAxisAlignment.CENTER),
        status
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    p1 = ft.Column([
        ft.Text("التحكم في الحركة", size=18, weight=ft.FontWeight.BOLD),
        btn("أمام", "F", ft.Icons.ARROW_UPWARD),
        ft.Row([btn("يسار", "L", ft.Icons.ARROW_BACK), btn("يمين", "R", ft.Icons.ARROW_FORWARD)], alignment=ft.MainAxisAlignment.CENTER),
        btn("خلف", "B", ft.Icons.ARROW_DOWNWARD),
        btn("توقف", "S", color=ft.Colors.RED_900)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)

    reply_txt = ft.Text("رد الروبوت: ...", color=ft.Colors.AMBER)
    def speak(e):
        r = random.choice(["حاضر", "تمام", "شكراً", "لا"])
        reply_txt.value = f"رد الروبوت: {r}"
        page.run_task(send, "SPK", r)

    def toggle_pwr(e):
        nonlocal power_on
        power_on = not power_on
        e.control.text = "إيقاف الروبوت" if power_on else "تشغيل الروبوت"
        e.control.bgcolor = ft.Colors.RED_700 if power_on else ft.Colors.GREEN_700
        page.run_task(send, "ON" if power_on else "OFF", e.control.text)

    p2 = ft.Column([
        ft.Text("الأوامر والصوتيات", size=18, weight=ft.FontWeight.BOLD),
        btn("الكلكس", "HORN", ft.Icons.CAMPAIGN, w=240),
        btn("الميكروفون", "MIC", ft.Icons.MIC, w=240),
        ft.ElevatedButton("الإسبيكر (رد الروبوت)", icon=ft.Icons.VOLUME_UP, width=240, on_click=speak),
        reply_txt,
        btn("الضوء", "LIGHT", ft.Icons.LIGHTBULB, w=240),
        ft.ElevatedButton("تشغيل الروبوت", icon=ft.Icons.POWER_SETTINGS_NEW, width=240, bgcolor=ft.Colors.GREEN_700, on_click=toggle_pwr)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    p3 = ft.Column([
        ft.Text("التحكم في الأطراف", size=18, weight=ft.FontWeight.BOLD),
        ft.Text("الرأس"),
        ft.Row([btn("رأس شمال", "HL"), btn("رأس يمين", "HR")], alignment=ft.MainAxisAlignment.CENTER),
        ft.Text("اليد اليمنى"),
        ft.Row([btn("يمنى فوق", "RU"), btn("يمنى تحت", "RD")], alignment=ft.MainAxisAlignment.CENTER),
        ft.Text("اليد اليسرى"),
        ft.Row([btn("يسرى فوق", "LU"), btn("يسرى تحت", "LD")], alignment=ft.MainAxisAlignment.CENTER),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    radar_txt = ft.Text("الطريق آمن", weight=ft.FontWeight.BOLD)
    radar_box = ft.Container(width=180, height=180, bgcolor=ft.Colors.GREEN_900, border_radius=12, alignment=ft.alignment.center, content=radar_txt)

    def test_radar(e):
        nonlocal obstacle
        obstacle = not obstacle
        radar_box.bgcolor = ft.Colors.RED_800 if obstacle else ft.Colors.GREEN_900
        radar_txt.value = "تحذير! يوجد عائق" if obstacle else "الطريق آمن"
        if obstacle:
            haptic.heavy_impact()
        page.update()

    p4 = ft.Column([
        ft.Text("الرادار", size=18, weight=ft.FontWeight.BOLD),
        radar_box,
        ft.Row([btn("رادار شمال", "RL"), btn("رادار يمين", "RR")], alignment=ft.MainAxisAlignment.CENTER),
        ft.TextButton("تجربة إنذار العائق", on_click=test_radar)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    pages = [p1, p2, p3, p4]
    body = ft.Container(content=pages[0], expand=True, padding=10)

    page.navigation_bar = ft.NavigationBar(
        on_change=lambda e: (setattr(body, "content", pages[e.control.selected_index]), page.update()),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.GAMEPAD, label="الحركة"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS_VOICE, label="الأوامر"),
            ft.NavigationBarDestination(icon=ft.Icons.ACCESSIBILITY_NEW, label="الأطراف"),
            ft.NavigationBarDestination(icon=ft.Icons.RADAR, label="الرادار"),
        ]
    )

    page.add(header, body)

ft.run(main)
