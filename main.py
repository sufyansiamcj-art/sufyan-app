import flet as ft
import requests
import json
import urllib.parse
import urllib3
import sqlite3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعداد قاعدة البيانات المحلية SQLite ---
DB_NAME = "github_favorites.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_favorites_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM favorites")
    rows = cursor.fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]

def add_favorite_to_db(repo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO favorites (id, data) VALUES (?, ?)", (repo.get("id"), json.dumps(repo)))
    conn.commit()
    conn.close()

def remove_favorite_from_db(repo_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE id = ?", (repo_id,))
    conn.commit()
    conn.close()


def main(page: ft.Page):
    init_db()  # تهيئة قاعدة البيانات عند بدء التشغيل

    page.title = "مستكشف مشاريع GitHub - sufyan siam"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.scroll = "auto"  # تفعيل التمرير التلقائي للشاشة بالكامل للتجاوب

    fetched_repos_data = []

    # حقول البحث والتصفية
    query_input = ft.TextField(
        hint_text="بحث عن المشاريع",
        border=ft.InputBorder.NONE,
        expand=True,
        text_size=14
    )
    
    lang_input = ft.TextField(
        value="python",
        visible=False
    )

    repos_list = ft.ListView(expand=True, spacing=12)
    fav_list = ft.ListView(expand=True, spacing=12)
    developer_repos_list = ft.ListView(expand=True, spacing=12)
    
    progress_bar = ft.ProgressBar(visible=False)
    dev_progress_bar = ft.ProgressBar(visible=False)

    # عناصر الداشبورد
    stat_total_repos = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="blue400")
    stat_total_stars = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="amber400")
    stat_fav_count = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color="green400")
    
    top_repos_container = ft.Column(spacing=10, expand=True)

    # --- فتح رابط في المتصفح ---
    def open_url(url):
        if url:
            page.launch_url(url)

    # --- إدارة المفضلة بواسطة قاعدة البيانات ---
    def toggle_favorite(repo):
        repo_id = repo.get("id")
        favs = get_favorites_from_db()
        exists = any(item.get("id") == repo_id for item in favs)
        
        if exists:
            remove_favorite_from_db(repo_id)
            msg = "تمت إزالة المشروع من المفضلة"
        else:
            add_favorite_to_db(repo)
            msg = "تمت إضافة المشروع للمفضلة"
            
        load_favorites_tab()
        update_dashboard()
        
        if fetched_repos_data:
            repos_list.controls.clear()
            for r in fetched_repos_data:
                repos_list.controls.append(build_repo_card(r))
        
        snack = ft.SnackBar(ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- تحديث بيانات الداشبورد ---
    def update_dashboard():
        favs = get_favorites_from_db()
        total_repos = len(fetched_repos_data)
        total_stars = sum(r.get("stargazers_count", 0) for r in fetched_repos_data)
        fav_count = len(favs)

        stat_total_repos.value = f"{total_repos:,}"
        stat_total_stars.value = f"{total_stars:,}"
        stat_fav_count.value = f"{fav_count:,}"

        top_repos_container.controls.clear()
        
        top_5 = sorted(fetched_repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:5]
        max_stars = top_5[0].get("stargazers_count", 1) if top_5 else 1

        if top_5:
            top_repos_container.controls.append(
                ft.Text("⭐ أعلى 5 مشاريع حصولاً على النجوم:", weight=ft.FontWeight.BOLD, size=15)
            )
            for repo in top_5:
                name = repo.get("name", "غير معروف")
                stars = repo.get("stargazers_count", 0)
                ratio = stars / max_stars if max_stars > 0 else 0
                
                top_repos_container.controls.append(
                    ft.Container(
                        padding=10,
                        border_radius=8,
                        bgcolor="grey900",
                        content=ft.Column([
                            ft.Row([
                                ft.Text(name, weight=ft.FontWeight.BOLD, size=14, color="blue400"),
                                ft.Text(f"⭐ {stars:,}", weight=ft.FontWeight.BOLD, color="amber400"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.ProgressBar(value=ratio, color="amber400", bgcolor="grey800")
                        ], spacing=5)
                    )
                )
        else:
            top_repos_container.controls.append(
                ft.Text("لا توجد بيانات كافية لعرض الإحصائيات حالياً.", color="grey400")
            )

    # --- بناء بطاقة المشروع الرئيسية ---
    def build_repo_card(repo, is_fav_tab=False):
        name = repo["name"]
        owner_data = repo.get("owner", {}) if isinstance(repo.get("owner"), dict) else {}
        owner_name = owner_data.get("login", "غير معروف")
        avatar_url = owner_data.get("avatar_url", "")
        
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        desc = repo.get("description") or "لا يوجد وصف للمشروع."
        target_url = repo.get("html_url")

        favs = get_favorites_from_db()
        is_fav = any(item.get("id") == repo.get("id") for item in favs)

        fav_btn_text = "❌ إزالة" if is_fav_tab or is_fav else "⭐ المفضلة"

        return ft.Card(
            elevation=4,
            content=ft.Container(
                padding=12,
                border_radius=10,
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.CircleAvatar(
                                foreground_image_src=avatar_url,
                                radius=14,
                                content=ft.Text(owner_name[0].upper() if owner_name else "?")
                            ),
                            ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color="blue400"),
                        ]),
                        ft.Text(f"⭐ {stars:,}", color="amber400", weight=ft.FontWeight.BOLD)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                    
                    ft.Text(f"👤 المطور: {owner_name}  |  🍴 التفرعات: {forks:,}", size=12, color="grey400"),
                    ft.Text(desc, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, size=13),
                    
                    ft.Row([
                        ft.OutlinedButton(
                            fav_btn_text,
                            on_click=lambda e, r=repo: toggle_favorite(r)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            tooltip=f"فتح مستودع {name}",
                            on_click=lambda e: open_url(target_url)
                        ),
                        ft.ElevatedButton(
                            "التفاصيل الكاملة",
                            on_click=lambda e, r=repo: show_repo_details(r)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)
                ])
            )
        )

    # --- جلب وعرض مشاريع مطور معين ---
    def fetch_developer_repos(owner_name):
        developer_repos_list.controls.clear()
        dev_progress_bar.visible = True
        
        explore_view.visible = False
        dashboard_view.visible = False
        favorites_view.visible = False
        about_view.visible = False
        developer_repos_view.visible = True
        page.update()

        url = f"https://api.github.com/users/{owner_name}/repos?sort=stars&per_page=20"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            if res.status_code == 200:
                repos = res.json()
                if not repos:
                    developer_repos_list.controls.append(ft.Text(f"لا توجد مشاريع عامة للمطور {owner_name}.", size=16))
                else:
                    for repo in repos:
                        developer_repos_list.controls.append(build_repo_card(repo))
            else:
                developer_repos_list.controls.append(ft.Text("تعذر جلب مشاريع المطور", color="red400"))
        except Exception as err:
            developer_repos_list.controls.append(ft.Text(f"خطأ في الاتصال: {str(err)}", color="red400"))

        dev_progress_bar.visible = False
        page.update()

    # --- شاشة التفاصيل الكاملة ---
    def show_repo_details(repo):
        name = repo.get("name", "غير معروف")
        owner_data = repo.get("owner", {}) if isinstance(repo.get("owner"), dict) else {}
        owner_name = owner_data.get("login", "غير معروف")
        avatar_url = owner_data.get("avatar_url", "")

        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        language = repo.get("language") or "غير محددة"
        license_name = repo.get("license", {}).get("name") if repo.get("license") and isinstance(repo.get("license"), dict) else "بدون رخصة"
        default_branch = repo.get("default_branch", "main")
        
        created_at = repo.get("created_at", "")[:10] if repo.get("created_at") else "غير محدد"
        desc = repo.get("description") or "لا يوجد وصف متوفر لهذا المشروع."
        target_url = repo.get("html_url")

        def close_dialog(e):
            details_dialog.open = False
            page.update()

        def go_to_dev_repos(e):
            details_dialog.open = False
            page.update()
            fetch_developer_repos(owner_name)

        details_dialog = ft.AlertDialog(
            title=ft.Text(f"التفاصيل: {name}", weight=ft.FontWeight.BOLD, size=16),
            content=ft.Container(
                width=400,
                content=ft.Column([
                    ft.Container(
                        padding=10,
                        border_radius=8,
                        bgcolor="grey900",
                        content=ft.Row([
                            ft.CircleAvatar(
                                foreground_image_src=avatar_url,
                                radius=24,
                                content=ft.Text(owner_name[0].upper() if owner_name else "?")
                            ),
                            ft.Column([
                                ft.Text(f"👤 المطور: {owner_name}", weight=ft.FontWeight.BOLD, size=14),
                                ft.TextButton("📁 استعراض مشاريع المطور", on_click=go_to_dev_repos, style=ft.ButtonStyle(padding=0))
                            ], spacing=2, expand=True)
                        ])
                    ),
                    ft.Divider(),
                    ft.Row([
                        ft.Text(f"⭐ النجوم: {stars:,}", color="amber400", weight=ft.FontWeight.BOLD),
                        ft.Text(f"🍴 التفرعات: {forks:,}", color="blue400", weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                    ft.Text(f"💻 لغة البرمجة: {language}", size=13),
                    ft.Text(f"📜 الرخصة: {license_name}", size=13),
                    ft.Text(f"🌿 الفرع الرئيسي: {default_branch}", size=13),
                    ft.Text(f"📅 الإنشاء: {created_at}", size=12, color="grey400"),
                    ft.Divider(),
                    ft.Text("الوصف:", weight=ft.FontWeight.BOLD),
                    ft.Text(desc, size=13, selectable=True),
                ], tight=True, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.ElevatedButton("🌐 فتح على GitHub", on_click=lambda e: open_url(target_url)),
                ft.TextButton("إغلاق", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(details_dialog)
        details_dialog.open = True
        page.update()

    # --- تحميل المفضلة ---
    def load_favorites_tab():
        fav_list.controls.clear()
        favs = get_favorites_from_db()
        if not favs:
            fav_list.controls.append(ft.Text("لا توجد مشاريع مضافة للمفضلة حالياً.", size=16))
        else:
            for repo in favs:
                fav_list.controls.append(build_repo_card(repo, is_fav_tab=True))
        page.update()

    # --- جلب البيانات ---
    def fetch_repos(e=None):
        nonlocal fetched_repos_data
        repos_list.controls.clear()
        progress_bar.visible = True
        page.update()

        search_query = query_input.value.strip()
        lang = lang_input.value.strip()

        q_parts = []
        if search_query:
            q_parts.append(search_query)
        if lang:
            q_parts.append(f"language:{lang}")
            
        full_query = " ".join(q_parts) if q_parts else "stars:>1000"
        encoded_query = urllib.parse.quote(full_query)
        
        url = f"https://api.github.com/search/repositories?q={encoded_query}&sort=stars&order=desc&per_page=15"
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            if res.status_code == 200:
                data = res.json()
                items = data.get("items", [])
                fetched_repos_data = items

                if not items:
                    repos_list.controls.append(ft.Text("لم يتم العثور على نتائج.", size=16))
                else:
                    for repo in items:
                        repos_list.controls.append(build_repo_card(repo))
            else:
                repos_list.controls.append(ft.Text("خطأ في الاتصال أو تجاوز الحد المسموح.", color="red400"))
        except Exception as err:
            repos_list.controls.append(ft.Text(f"خطأ: {str(err)}", color="red400"))

        progress_bar.visible = False
        update_dashboard()
        page.update()

    # --- الثيم ---
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon.icon = ft.Icons.LIGHT_MODE
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon.icon = ft.Icons.DARK_MODE
        page.update()

    theme_icon = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_size=20,
        tooltip="تغيير المظهر",
        on_click=toggle_theme
    )

    # --- واجهة الداشبورد ---
    dashboard_view = ft.Column([
        ft.Text("📈 لوحة التحكم والإحصائيات", size=18, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.Card(content=ft.Container(padding=10, content=ft.Column([ft.Text("النتائج", size=11, color="grey400"), stat_total_repos], alignment=ft.MainAxisAlignment.CENTER), width=100)),
            ft.Card(content=ft.Container(padding=10, content=ft.Column([ft.Text("النجوم", size=11, color="grey400"), stat_total_stars], alignment=ft.MainAxisAlignment.CENTER), width=105)),
            ft.Card(content=ft.Container(padding=10, content=ft.Column([ft.Text("المفضلة", size=11, color="grey400"), stat_fav_count], alignment=ft.MainAxisAlignment.CENTER), width=100)),
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True),
        ft.Divider(),
        top_repos_container
    ], expand=True, visible=False)

    # --- واجهة عن التطبيق ---
    about_view = ft.Column([
        ft.Container(
            padding=20,
            border_radius=12,
            bgcolor="grey900",
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CODE, size=30, color="blue400"), ft.Text("مشاريع GitHub", size=18, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                ft.Divider(),
                ft.Text("مطور برمجيات شغوف بابتكار وتطوير الحلول التقنية الحديثة واجهات تفاعلية.", size=13, color="grey300"),
                ft.Divider(),
                ft.Row([ft.Icon(ft.Icons.PERSON, color="blue400"), ft.Text("المطور: سفيان ابراهيم صيام", size=14, weight=ft.FontWeight.BOLD)], wrap=True),
                ft.Row([ft.Icon(ft.Icons.EMAIL, color="green400"), ft.Text("sufyansiam.cj@gmail.com", size=13, weight=ft.FontWeight.BOLD)], wrap=True),
            ], spacing=10)
        )
    ], expand=True, visible=False, alignment=ft.MainAxisAlignment.CENTER)

    # --- واجهة مشاريع المطور ---
    def back_to_explore(e):
        developer_repos_view.visible = False
        explore_view.visible = True
        page.update()

    developer_repos_view = ft.Column([
        ft.Row([ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=back_to_explore), ft.Text("📁 مشاريع المطور", size=16, weight=ft.FontWeight.BOLD)], wrap=True),
        dev_progress_bar,
        ft.Divider(),
        developer_repos_list
    ], expand=True, visible=False)

    # --- التبديل بين التبويبات وتغيير شكل الأزرار ---
    def switch_tab(e):
        target = e.control.data
        explore_view.visible = (target == "explore")
        favorites_view.visible = (target == "fav")
        dashboard_view.visible = (target == "dashboard")
        about_view.visible = (target == "about")
        developer_repos_view.visible = False
        
        for btn in [btn_explore, btn_dashboard, btn_fav, btn_about]:
            if btn.data == target:
                btn.bgcolor = "blue900"
            else:
                btn.bgcolor = "grey900"

        if target == "fav":
            load_favorites_tab()
        elif target == "dashboard":
            update_dashboard()
        page.update()

    btn_explore = ft.IconButton(icon=ft.Icons.GRID_VIEW, data="explore", on_click=switch_tab, bgcolor="blue900", tooltip="المشاريع")
    btn_dashboard = ft.IconButton(icon=ft.Icons.DASHBOARD, data="dashboard", on_click=switch_tab, bgcolor="grey900", tooltip="الداشبورد")
    btn_fav = ft.IconButton(icon=ft.Icons.STAR, data="fav", on_click=switch_tab, bgcolor="grey900", tooltip="المفضلة")
    btn_about = ft.IconButton(icon=ft.Icons.INFO, data="about", on_click=switch_tab, bgcolor="grey900", tooltip="عن التطبيق")

    explore_view = ft.Column([
        ft.Container(
            padding=8,
            border_radius=25,
            bgcolor="grey900",
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.SEARCH, on_click=fetch_repos, icon_size=20),
                query_input,
                ft.IconButton(icon=ft.Icons.FILTER_LIST, icon_size=20, tooltip="تصفية")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        progress_bar,
        ft.Divider(),
        repos_list
    ], expand=True)

    favorites_view = ft.Column([ft.Divider(), fav_list], expand=True, visible=False)

    # إعداد الواجهة مع تحديث العنوان العلوي إلى sufyan siam
    page.add(
        ft.Container(
            padding=8,
            content=ft.Row([
                ft.Row([
                    ft.CircleAvatar(
                        content=ft.Text("S", weight=ft.FontWeight.BOLD),
                        radius=16,
                        bgcolor="blue700"
                    ),
                    ft.Column([
                        ft.Text("sufyan siam's", size=12, weight=ft.FontWeight.BOLD, color="grey400"),
                        ft.Text("Projects", size=14, weight=ft.FontWeight.BOLD)
                    ], spacing=0)
                ], spacing=8),
                ft.Text("GitHub 🚀", size=16, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        
        ft.Row([
            ft.Row([btn_explore, btn_dashboard, btn_fav, btn_about], spacing=5),
            theme_icon
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        ft.Divider(height=15),
        explore_view,
        dashboard_view,
        favorites_view,
        about_view,
        developer_repos_view
    )

    fetch_repos()

ft.app(target=main)
