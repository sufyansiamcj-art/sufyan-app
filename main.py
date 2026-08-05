import datetime
import time
import threading
import urllib.request
import json
import flet as ft

# دعم مكتبة adhanpy لحساب مواقيت الصلاة
try:
    from adhanpy import Coordinates, CalculationMethod, CalculationParameters, PrayerTimes
    USE_ADHANPY = True
except Exception:
    USE_ADHANPY = False


def get_current_location_coords():
    """جلب إحداثيات الموقع الحالي تلقائياً"""
    try:
        url = "http://ip-api.com/json/"
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read().decode())
        if data.get("status") == "success":
            return float(data["lat"]), float(data["lon"]), f"{data.get('city')}, {data.get('country')}"
    except Exception:
        pass
    return 32.8908, 13.1796, "Tripoli, Libya"


def set_do_not_disturb(enable: bool):
    """تفعيل أو إلغاء وضع الصامت"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        
        activity = PythonActivity.mActivity
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)
        
        if nm and nm.isNotificationPolicyAccessGranted():
            if enable:
                nm.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_PRIORITY)
            else:
                nm.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL)
    except Exception as e:
        print(f"[DND Test]: {enable} | Error: {e}")


def get_prayer_times_data(lat, lon):
    """حساب مواقيت الصلاة لليوم بناءً على الإحداثيات"""
    now = datetime.datetime.now()
    today = datetime.date.today()
    
    if USE_ADHANPY:
        try:
            coordinates = Coordinates(lat, lon)
            params = CalculationParameters(CalculationMethod.MUSLIM_WORLD_LEAGUE)
            pt = PrayerTimes(coordinates, today, params)
            return [
                ("الفجر", pt.fajr),
                ("الظهر", pt.dhuhr),
                ("العصر", pt.asr),
                ("المغرب", pt.maghrib),
                ("العشاء", pt.isha),
            ]
        except Exception as e:
            print(f"Adhanpy Exception: {e}")
            
    return [
        ("الفجر", now.replace(hour=5, minute=0, second=0)),
        ("الظهر", now.replace(hour=12, minute=30, second=0)),
        ("العصر", now.replace(hour=15, minute=45, second=0)),
        ("المغرب", now.replace(hour=18, minute=30, second=0)),
        ("العشاء", now.replace(hour=20, minute=0, second=0)),
    ]


def main(page: ft.Page):
    page.title = "سكينة - وضع الصلاة الذكي"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.rtl = True
    
    dnd_duration_mins = 25
    is_monitoring = False

    lat_input = ft.TextField(label="خط العرض (Lat)", value="32.8908", expand=True, border_radius=10)
    lon_input = ft.TextField(label="خط الطول (Lon)", value="13.1796", expand=True, border_radius=10)
    location_label = ft.Text("الموقع: Tripoli, Libya", size=13, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500)
    
    status_text = ft.Text("المراقبة معطلة حالياً", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800)
    next_prayer_container = ft.Container(padding=15, border_radius=15)
    times_list = ft.Column(spacing=10)

    def update_status(msg, color=ft.Colors.BLUE_700):
        status_text.value = msg
        status_text.color = color
        page.update()

    def calculate_prayers():
        try:
            lat = float(lat_input.value)
            lon = float(lon_input.value)
            prayers = get_prayer_times_data(lat, lon)
            
            times_list.controls.clear()
            now = datetime.datetime.now()
            next_found = False

            for name, p_time in prayers:
                p_dt = p_time if isinstance(p_time, datetime.datetime) else datetime.datetime.combine(now.date(), p_time.time())
                time_str = p_dt.strftime("%I:%M %p")
                
                is_next = False
                if not next_found and p_dt > now:
                    is_next = True
                    next_found = True
                    diff_mins = int((p_dt - now).total_seconds() // 60)
                    
                    next_prayer_container.content = ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("الصلاة القادمة", size=12, color=ft.Colors.WHITE70),
                                    ft.Text(f"{name}", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                    ft.Text(f"الوقت: {time_str}", size=14, color=ft.Colors.WHITE),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(ft.Icons.TIMER_ROUNDED, color=ft.Colors.WHITE, size=28),
                                        ft.Text(f"{diff_mins // 60} س و {diff_mins % 60} د", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                bgcolor=ft.Colors.WHITE12,
                                padding=10,
                                border_radius=10,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    )
                    next_prayer_container.bgcolor = ft.Colors.INDIGO_700

                times_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.ACCESS_TIME_FILLED if is_next else ft.Icons.ACCESS_TIME, 
                                            color=ft.Colors.INDIGO_600 if is_next else ft.Colors.GREY_500),
                                    ft.Text(name, size=16, weight=ft.FontWeight.BOLD if is_next else ft.FontWeight.NORMAL),
                                ]),
                                ft.Text(time_str, size=16, weight=ft.FontWeight.BOLD if is_next else ft.FontWeight.NORMAL,
                                        color=ft.Colors.INDIGO_700 if is_next else ft.Colors.BLACK87),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=15,
                        bgcolor=ft.Colors.INDIGO_50 if is_next else ft.Colors.WHITE,
                        border_radius=12,
                        border=ft.border.all(1, ft.Colors.INDIGO_200 if is_next else ft.Colors.GREY_200)
                    )
                )
            page.update()
        except Exception as err:
            update_status(f"خطأ: {err}", ft.Colors.RED)

    def auto_detect_location(e=None):
        lat, lon, city = get_current_location_coords()
        lat_input.value = str(lat)
        lon_input.value = str(lon)
        location_label.value = f"الموقع المحدد: {city}"
        calculate_prayers()

    def prayer_monitor_loop():
        nonlocal is_monitoring
        while is_monitoring:
            try:
                lat = float(lat_input.value)
                lon = float(lon_input.value)
                now = datetime.datetime.now()
                prayers = get_prayer_times_data(lat, lon)
                
                for name, p_time in prayers:
                    p_dt = p_time if isinstance(p_time, datetime.datetime) else datetime.datetime.combine(now.date(), p_time.time())
                    diff = (p_dt - now).total_seconds()
                    
                    if -30 <= diff <= 60:
                        update_status(f"حان وقت صلاة {name}! تم تفعيل الصامت.", ft.Colors.RED_600)
                        set_do_not_disturb(True)
                        time.sleep(dnd_duration_mins * 60)
                        set_do_not_disturb(False)
                        update_status("انتهت الصلاة، تم إلغاء الوضع الصامت.", ft.Colors.GREEN_600)
            except Exception:
                pass
            time.sleep(20)

    def toggle_monitoring(e):
        nonlocal is_monitoring
        if not is_monitoring:
            is_monitoring = True
            btn_toggle.text = "إيقاف المراقبة"
            btn_toggle.icon = ft.Icons.STOP_ROUNDED
            btn_toggle.style = ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED_600)
            update_status("المراقبة شغالة ومستمرة...", ft.Colors.GREEN_700)
            threading.Thread(target=prayer_monitor_loop, daemon=True).start()
        else:
            is_monitoring = False
            btn_toggle.text = "بدء المراقبة"
            btn_toggle.icon = ft.Icons.PLAY_ARROW_ROUNDED
            btn_toggle.style = ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.INDIGO_600)
            update_status("تم إيقاف المراقبة", ft.Colors.ORANGE_800)
        page.update()

    btn_calc = ft.OutlinedButton("تحديث المواقيت", icon=ft.Icons.REFRESH_ROUNDED, on_click=lambda _: calculate_prayers())
    btn_toggle = ft.ElevatedButton("بدء المراقبة", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=toggle_monitoring,
                                   style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.INDIGO_600))

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.MOSQUE, size=50, color=ft.Colors.WHITE),
                    ft.Text("سكينة - وضع الصلاة", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.INDIGO_700,
                padding=20,
                height=150,
            ),
            ft.NavigationDrawerDestination(
                icon=ft.Icons.MY_LOCATION,
                label="تحديد الموقع تلقائياً",
            ),
            ft.Divider(),
            ft.Container(
                content=ft.Text("تطبيق ود صيام الذكي v1.0", size=12, color=ft.Colors.GREY_500),
                padding=15
            )
        ],
        on_change=lambda e: auto_detect_location() if e.data == "0" else None
    )

    page.appbar = ft.AppBar(
        leading=ft.IconButton(ft.Icons.MENU, on_click=lambda _: page.open(page.drawer)),
        title=ft.Text("تطبيق ود صيام الصامت", weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.INDIGO_700,
        color=ft.Colors.WHITE,
        center_title=True
    )

    page.add(
        ft.Container(
            padding=15,
            content=ft.Column([
                next_prayer_container,
                ft.Container(height=5),
                ft.Row([lat_input, lon_input]),
                location_label,
                ft.Row([btn_calc, btn_toggle], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                ft.Container(height=5),
                ft.Container(content=status_text, padding=10, bgcolor=ft.Colors.GREY_100, border_radius=8),
                ft.Text("مواقيت الصلاة لليوم:", size=16, weight=ft.FontWeight.BOLD),
                times_list
            ], spacing=12)
        )
    )

    auto_detect_location()

ft.run(main)
