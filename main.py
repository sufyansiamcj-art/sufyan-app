import datetime
import time
import threading
import flet as ft

# دعم كافة طرق استيراد adhanpy
try:
    from adhanpy import Coordinates, CalculationMethod, CalculationParameters, PrayerTimes
    USE_ADHANPY = True
except Exception:
    USE_ADHANPY = False


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
            
    # مواقيت تجريبية في حال تعذر المكتبة
    return [
        ("الفجر", now.replace(hour=5, minute=0, second=0)),
        ("الظهر", now.replace(hour=12, minute=30, second=0)),
        ("العصر", now.replace(hour=15, minute=45, second=0)),
        ("المغرب", now.replace(hour=18, minute=30, second=0)),
        ("العشاء", now.replace(hour=20, minute=0, second=0)),
    ]


def set_do_not_disturb(enable: bool):
    """
    تفعيل أو إلغاء وضع عدم الإزعاج
    ملاحظة: تعمل على أندرويد عبر PyJnius، وعلى الكمبيوتر تكتفي بالطباعة للتجربة
    """
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
        # وضع محاكاة للتجربة على الكمبيوتر (Desktop Test Mode)
        state_str = "تفعيل [وضع عدم الإزعاج]" if enable else "إلغاء [وضع عدم الإزعاج]"
        print(f"[محاكاة النظام]: تم {state_str}")


def main(page: ft.Page):
    page.title = "مواقيت الصلاة ووضع الصامت"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # عناصر واجهة المستخدم
    lat_input = ft.TextField(
        label="خط العرض (Latitude)", 
        value="32.8872", 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    lon_input = ft.TextField(
        label="خط الطول (Longitude)", 
        value="13.1913", 
        keyboard_type=ft.KeyboardType.NUMBER
    )

    status_text = ft.Text(
        "المراقبة معطلة حالياً", 
        size=14, 
        weight=ft.FontWeight.BOLD, 
        color=ft.Colors.ORANGE_800
    )
    
    times_list = ft.Column(spacing=10)
    is_monitoring = False

    def update_status(msg, color=ft.Colors.BLUE_700):
        status_text.value = msg
        status_text.color = color
        page.update()

    def prayer_monitor_loop(lat, lon):
        """خيط المراقبة المستمر في الخلفية"""
        nonlocal is_monitoring
        while is_monitoring:
            now = datetime.datetime.now()
            prayers = get_prayer_times_data(lat, lon)
            
            for name, p_time in prayers:
                # التأكد من مطابقة الوقت
                p_datetime = p_time if isinstance(p_time, datetime.datetime) else datetime.datetime.combine(now.date(), p_time.time())
                
                # الفارق الزمني بالثواني بين الوقت الحالي ووقت الصلاة
                diff = (p_datetime - now).total_seconds()
                
                # إذا وصلنا لوقت الصلاة (في نطاق دقيقة)
                if 0 <= diff <= 60:
                    update_status(f"حان وقت صلاة {name}! تم تفعيل الصامت.", ft.Colors.RED_600)
                    set_do_not_disturb(True)
                    
                    # 15 دقيقة وقت الصلاة + 10 دقائق بعدها = 25 دقيقة (1500 ثانية)
                    duration = 25 * 60 
                    time.sleep(duration)
                    
                    set_do_not_disturb(False)
                    update_status("انتهت الصلاة، تم إلغاء الوضع الصامت.", ft.Colors.GREEN_600)
            
            # فحص كل 30 ثانية
            time.sleep(30)

    def toggle_monitoring(e):
        nonlocal is_monitoring
        try:
            lat = float(lat_input.value)
            lon = float(lon_input.value)
            
            if not is_monitoring:
                is_monitoring = True
                btn_toggle.text = "إيقاف المراقبة"
                btn_toggle.icon = ft.Icons.STOP
                btn_toggle.style = ft.ButtonStyle(color=ft.Colors.RED)
                update_status("المراقبة شغالّة ومستمرة في الخلفية...", ft.Colors.GREEN_700)
                
                # تشغيل المراقبة في خيط منفصل (Background Thread)
                threading.Thread(target=prayer_monitor_loop, args=(lat, lon), daemon=True).start()
            else:
                is_monitoring = False
                btn_toggle.text = "بدء المراقبة التلقائية"
                btn_toggle.icon = ft.Icons.PLAY_ARROW
                btn_toggle.style = ft.ButtonStyle(color=ft.Colors.BLUE)
                update_status("تم إيقاف المراقبة", ft.Colors.ORANGE_800)
                
            page.update()
        except ValueError:
            update_status("يرجى إدخال إحداثيات صحيحة", ft.Colors.RED)

    def calculate_prayers(e=None):
        try:
            lat = float(lat_input.value)
            lon = float(lon_input.value)
            prayers = get_prayer_times_data(lat, lon)
            
            times_list.controls.clear()
            for name, p_time in prayers:
                time_str = p_time.strftime("%I:%M %p") if hasattr(p_time, 'strftime') else str(p_time)
                times_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(name, size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(time_str, size=18, color=ft.Colors.BLUE_700),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            padding=15
                        )
                    )
                )
            page.update()
        except Exception as err:
            update_status(f"خطأ: {err}", ft.Colors.RED)

    btn_calc = ft.ElevatedButton("تحديث المواقيت", icon=ft.Icons.REFRESH, on_click=calculate_prayers)
    btn_toggle = ft.ElevatedButton("بدء المراقبة التلقائية", icon=ft.Icons.PLAY_ARROW, on_click=toggle_monitoring)

    page.add(
        ft.Column(
            [
                ft.Text("تطبيق ود صيام لوضع الصلاة الذكي", size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                lat_input,
                lon_input,
                ft.Row([btn_calc, btn_toggle], alignment=ft.MainAxisAlignment.CENTER),
                ft.Divider(),
                ft.Card(
                    content=ft.Container(
                        content=status_text,
                        padding=15
                    )
                ),
                ft.Text("مواقيت الصلاة لليوم:", size=16, weight=ft.FontWeight.BOLD),
                times_list
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

    calculate_prayers()

ft.run(main)