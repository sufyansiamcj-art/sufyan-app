import datetime
import time
import threading
import urllib.request
import json
import flet as ft

# دعم adhanpy لحساب مواقيت الصلاة
try:
    from adhanpy import Coordinates, CalculationMethod, CalculationParameters, PrayerTimes
    USE_ADHANPY = True
except Exception:
    USE_ADHANPY = False


def get_current_location_coords():
    """جلب إحداثيات الموقع الحالي تلقائياً عبر خدمة IP"""
    try:
        url = "http://ip-api.com/json/"
        req = urllib.request.urlopen(url, timeout=5)
        data = json.loads(req.read().decode())
        if data.get("status") == "success":
            return float(data["lat"]), float(data["lon"]), f"{data.get('city')}, {data.get('country')}"
    except Exception:
        pass
    return 32.8872, 13.1913, "موقع افتراضي"


def request_dnd_permission():
    """فتح إعدادات الأندرويد لمنح إذن وضع عدم الإزعاج"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        
        intent = Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS)
        activity = PythonActivity.mActivity
        activity.startActivity(intent)
        return True
    except Exception as e:
        print(f"DND Permission Request Error: {e}")
        return False


def set_do_not_disturb(enable: bool):
    """تفعيل أو إلغاء وضع عدم الإزعاج"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        NotificationManager = autoclass('android.app.NotificationManager')
        
        activity = PythonActivity.mActivity
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)
        
        if nm.isNotificationPolicyAccessGranted():
            if enable:
                nm.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_PRIORITY)
            else:
                nm.setInterruptionFilter(NotificationManager.INTERRUPTION_FILTER_ALL)
    except Exception:
        state_str = "تفعيل [وضع الصامت]" if enable else "إلغاء [وضع الصامت]"
        print(f"[محاكاة النظام]: تم {state_str}")


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
        except Exception:
            pass
            
    return [
        ("الفجر", now.replace(hour=5, minute=0, second=0)),
        ("الظهر", now.replace(hour=12, minute=30, second=0)),
        ("العصر", now.replace(hour=15, minute=45, second=0)),
        ("المغرب", now.replace(hour=18, minute=30, second=0)),
        ("العشاء", now.replace(hour=20, minute=0, second=0)),
    ]


def main(page: ft.Page):
    page.title = "مواقيت الصلاة ووضع الصامت"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # متغيرة الإعدادات
    dnd_duration_mins = 25

    # عناصر واجهة الإحداثيات والموقع
    lat_input = ft.TextField(label="خط العرض (Lat)", value="32.8872", expand=True)
    lon_input = ft.TextField(label="خط الطول (Lon)", value="13.1913", expand=True)
    location_label = ft.Text("الموقع: جاري التحديد...", size=12, italic=True, color=ft.Colors.GREY_700)

    # حقل الصلاة القادمة والإعدادات
    next_prayer_card = ft.Card(content=ft.Container(padding=15))
    status_text = ft.Text("المراقبة معطلة حالياً", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_800)
    times_list = ft.Column(spacing=8)
    
    is_monitoring = False

    def update_status(msg, color=ft.Colors.BLUE_700):
        status_text.value = msg
        status_text.color = color
        page.update()

    def get_next_prayer(prayers):
        now = datetime.datetime.now()
        for name, p_time in prayers:
            p_datetime = p_time if isinstance(p_time, datetime.datetime) else datetime.datetime.combine(now.date(), p_time.time())
            if p_datetime > now:
                return name, p_datetime
        # في حال انتهت صلوات اليوم، الصلاة القادمة هي الفجر للغد
        fajr_name, fajr_time = prayers[0]
        next_fajr = (fajr_time if isinstance(fajr_time, datetime.datetime) else datetime.datetime.combine(now.date(), fajr_time.time())) + datetime.timedelta(days=1)
        return fajr_name, next_fajr

    def calculate_prayers(e=None):
        try:
            lat = float(lat_input.value)
            lon = float(lon_input.value)
            prayers = get_prayer_times_data(lat, lon)
            
            # تحديد الصلاة القادمة
            next_name, next_dt = get_next_prayer(prayers)
            diff_mins = int((next_dt - datetime.datetime.now()).total_seconds() // 60)
            
            next_prayer_card.content = ft.Container(
                content=ft.Column([
                    ft.Text("الصلاة القادمة", size=14, color=ft.Colors.WHITE70),
                    ft.Text(f"{next_name} - {next_dt.strftime('%I:%M %p')}", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text(f"متبقي: {diff_mins // 60} ساعة و {diff_mins % 60} دقيقة", size=12, color=ft.Colors.WHITE),
                ], alignment=ft.MainAxisAlignment.CENTER),
                bg_color=ft.Colors.BLUE_800,
                padding=15,
                border_radius=10
            )

            times_list.controls.clear()
            for name, p_time in prayers:
                time_str = p_time.strftime("%I:%M %p") if hasattr(p_time, 'strftime') else str(p_time)
                is_next = (name == next_name)
                times_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Text(name, size=16, weight=ft.FontWeight.BOLD if is_next else ft.FontWeight.NORMAL),
                                ft.Text(time_str, size=16, color=ft.Colors.BLUE_700 if is_next else ft.Colors.BLACK),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=12,
                            border_radius=8
                        )
                    )
                )
            page.update()
        except Exception as err:
            update_status(f"خطأ: {err}", ft.Colors.RED)

    def auto_detect_location(e=None):
        update_status("جاري جلب الموقع الجغرافي...", ft.Colors.BLUE)
        lat, lon, city = get_current_location_coords()
        lat_input.value = str(lat)
        lon_input.value = str(lon)
        location_label.value = f"الموقع المحدد: {city}"
        calculate_prayers()
        update_status("تم تحديث الموقع بنجاح", ft.Colors.GREEN_700)

    def prayer_monitor_loop():
        nonlocal is_monitoring
        while is_monitoring:
            try:
                lat = float(lat_input.value)
                lon = float(lon_input.value)
                now = datetime.datetime.now()
                prayers = get_prayer_times_data(lat, lon)
                
                for name, p_time in prayers:
                    p_datetime = p_time if isinstance(p_time, datetime.datetime) else datetime.datetime.combine(now.date(), p_time.time())
                    diff = (p_datetime - now).total_seconds()
                    
                    if 0 <= diff <= 60:
                        update_status(f"حان وقت صلاة {name}! تم تفعيل الصامت.", ft.Colors.RED_600)
                        set_do_not_disturb(True)
                        time.sleep(dnd_duration_mins * 60)
                        set_do_not_disturb(False)
                        update_status("انتهت الصلاة، تم إلغاء الوضع الصامت.", ft.Colors.GREEN_600)
            except Exception:
                pass
            time.sleep(30)

    def toggle_monitoring(e):
        nonlocal is_monitoring
        if not is_monitoring:
            is_monitoring = True
            btn_toggle.text = "إيقاف المراقبة"
            btn_toggle.icon = ft.Icons.STOP
            btn_toggle.style = ft.ButtonStyle(color=ft.Colors.RED)
            update_status("المراقبة شغالة ومستمرة...", ft.Colors.GREEN_700)
            threading.Thread(target=prayer_monitor_loop, daemon=True).start()
        else:
            is_monitoring = False
            btn_toggle.text = "بدء المراقبة"
            btn_toggle.icon = ft.Icons.PLAY_ARROW
            btn_toggle.style = ft.ButtonStyle(color=ft.Colors.BLUE)
            update_status("تم إيقاف المراقبة", ft.Colors.ORANGE_800)
        page.update()

    # الأزرار
    btn_calc = ft.ElevatedButton("تحديث الموقع والمواقيت", icon=ft.Icons.MY_LOCATION, on_click=auto_detect_location)
    btn_toggle = ft.ElevatedButton("بدء المراقبة", icon=ft.Icons.PLAY_ARROW, on_click=toggle_monitoring)
    btn_perm = ft.OutlinedButton("تفعيل إذن وضع الصامت (DND)", icon=ft.Icons.SECURITY, on_click=lambda _: request_dnd_permission())

    # بناء واجهة التطبيق
    page.add(
        ft.Column([
            ft.Text("تطبيق ود صيام لوضع الصلاة الذكي", size=20, weight=ft.FontWeight.BOLD),
            btn_perm,
            ft.Divider(),
            next_prayer_card,
            ft.Row([lat_input, lon_input]),
            location_label,
            ft.Row([btn_calc, btn_toggle], alignment=ft.MainAxisAlignment.CENTER),
            ft.Card(content=ft.Container(content=status_text, padding=10)),
            ft.Text("مواقيت الصلاة لليوم:", size=16, weight=ft.FontWeight.BOLD),
            times_list
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    # تشغيل جلب الموقع والمواقيت عند الفتح
    auto_detect_location()

ft.run(main)
