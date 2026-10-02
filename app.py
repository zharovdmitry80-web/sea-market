import os
import sqlite3
import re
import urllib.request
import flet as ft

SEA_BG = "#D4EDF7"
SEA_WAVE = "#BCE0F0"
BRAND_BLUE = "#4BB4D4"
BRAND_DARK = "#0F4C64"
CORAL_BTN = "#FF6B4A"
RED_ALERT = "#DC2626"
GREEN = "#10B981"
PURPLE = "#7C3AED"
WHITE = "#FFFFFF"
BLACK = "#000000"
YELLOW = "#FFE600"
MUTED = "#475569"

CARD_STYLES = {
    "Бронза":  {"bg": "#B87333", "rim": "#8A5220", "cashback": "3%",  "icon": "🥉"},
    "Серебро": {"bg": "#607D8B", "rim": "#37474F", "cashback": "5%",  "icon": "🥈"},
    "Золото":  {"bg": "#D4AF37", "rim": "#9A7B1C", "cashback": "10%", "icon": "🥇"},
}

PRODUCTS = {
    "Креветки королевские": {"price": 690, "old_price": 890, "weight": "1 кг", "icon": "🦐", "cat": "Морепродукты и рыба", "is_promo": True, "promo_until": "до 12 октября"},
    "Минтай Borealis филе": {"price": 399, "old_price": 499, "weight": "400 г", "icon": "🐟", "cat": "Морепродукты и рыба", "is_promo": True, "promo_until": "до 10 октября"},
    "Форель слабосолёная": {"price": 540, "old_price": 680, "weight": "300 г", "icon": "🍣", "cat": "Морепродукты и рыба", "is_promo": True, "promo_until": "до 15 октября"},
    "Скумбрия атлантическая": {"price": 190, "old_price": 190, "weight": "300 г", "icon": "🐟", "cat": "Морепродукты и рыба", "is_promo": False, "promo_until": ""},
    "Напиток Evervess Кола": {"price": 109, "old_price": 149, "weight": "1 л", "icon": "🥤", "cat": "Напитки и вода", "is_promo": True, "promo_until": "до конца недели"},
    "Вода родниковая": {"price": 45, "old_price": 45, "weight": "1,5 л", "icon": "💧", "cat": "Напитки и вода", "is_promo": False, "promo_until": ""},
    "Хачапури с сыром": {"price": 79, "old_price": 79, "weight": "120 г", "icon": "🥐", "cat": "К столу и десерты", "is_promo": False, "promo_until": ""},
    "Чиабатта пшеничная": {"price": 65, "old_price": 65, "weight": "200 г", "icon": "🥖", "cat": "К столу и десерты", "is_promo": False, "promo_until": ""},
}

DB_NAME = "market.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, role TEXT, password TEXT, deliveries INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS stores (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT, hours TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone = '+79950057432'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (name, phone, role, password, deliveries) VALUES (?, ?, ?, ?, ?)", ("Дмитрий Жаров", "+79950057432", "Владелец", "12345", 0))
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM stores")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stores (name, address, hours) VALUES ('Морские Деликатесы №1 (Северная)', 'г. Краснодар, ул. 1-го Мая, 580/3', '08:00 – 22:00')")
        cursor.execute("INSERT INTO stores (name, address, hours) VALUES ('Морские Деликатесы №2 (Центр)', 'г. Краснодар, ул. Красная, 150', '08:00 – 23:00')")
    
    cursor.execute("SELECT value FROM settings WHERE key = 'tg_channel'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO settings (key, value) VALUES ('tg_channel', 'morskie_delikatesy')")
    conn.commit()
    conn.close()

init_db()

def get_db_setting(key, default=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def save_db_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def load_users_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone, role, password, deliveries FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "phone": r[2], "role": r[3], "password": r[4], "deliveries": r[5]} for r in rows]

def load_stores_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, hours FROM stores")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "address": r[2], "hours": r[3]} for r in rows]

def delete_user_from_db(uid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

def delete_store_from_db(sid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stores WHERE id = ?", (sid,))
    conn.commit()
    conn.close()

db = {
    "role": "Владелец", "tab": "Главная", "subscreen": None, "search_q": "",
    "fio": "Дмитрий Жаров", "phone": "+79950057432", "address": "Волховская улица, 8",
    "intercom": "Подъезд 2, кв. 45, домофон 45К1234", "time_slot": None, "slot_warning": False,
    "orders": 9, "status": "Золото", "bonuses": 2500, "spend_bonuses": False,
    "pay_methods": ["⚡ СБП (Система быстрых платежей)", "🟢 SberPay", "🟡 Т-Pay", "💳 Карта МИР •••• 6148"],
    "selected_pay": "⚡ СБП (Система быстрых платежей)",
    "cart": {"Креветки королевские": 1, "Минтай Borealis филе": 1},
    "gift_added": False, "promo_discount": 0, "comment": "Позвонить, если нужна замена",
    "categories": ["Морепродукты и рыба", "Напитки и вода", "К столу и десерты"],
    "owner_tab": "Каталог", "tg_channel": get_db_setting("tg_channel", "morskie_delikatesy"),
    "news_posts": [
        {
            "id": 1, "author": "📲 Telegram-канал @morskie_delikatesy", "date": "Сегодня",
            "text": "РЕЦЕПТ ГОТОВ 😋😋😋\nМидии, как в ресторане, только МНОГО И ВСЕГО ЗА 249₽! 🔥🔥🔥",
            "photo": "logo.jpg", "video": "Видео-рецепт приготовления мидий (00:45)", "is_tg": True
        }
    ],
    "orders_list": []
}

def clean_tg_link(raw_val):
    clean = raw_val.replace("https://t.me/", "").replace("http://t.me/", "").replace("@", "").strip().split("/")[0]
    return clean if clean else "morskie_delikatesy"

def sync_telegram_channel():
    clean_ch = clean_tg_link(db["tg_channel"])
    db["tg_channel"] = clean_ch
    save_db_setting("tg_channel", clean_ch)

def strike_price(val):
    s = f"{val}.00"
    return "".join(ch + "\u0336" for ch in s) + " ₽"

def get_promo_names():
    return [k for k, v in PRODUCTS.items() if v.get("is_promo", False)]

def white_field(label_txt="", val="", hint="", w=None):
    return ft.TextField(
        label=label_txt if label_txt else None, value=val, hint_text=hint if hint else None,
        color=BLACK, bgcolor=WHITE, filled=True, fill_color=WHITE,
        border_color=BRAND_BLUE, cursor_color=BLACK, width=w
    )

def logo(sz=36):
    if os.path.exists("logo.jpg"):
        return ft.Image(src="logo.jpg", width=sz, height=sz, border_radius=10)
    return ft.Container(content=ft.Text("🦐", size=18), width=sz, height=sz, bgcolor=BRAND_BLUE, border_radius=10)

def sea_divider(text_label):
    return ft.Container(
        bgcolor=SEA_WAVE, padding=8, border_radius=12,
        content=ft.Row([ft.Text("🌊 🫧", size=14), ft.Text(text_label, size=13, color=BRAND_DARK), ft.Text("🐚 🌊", size=14)], spacing=6)
    )

def status_badge(st):
    mapping = {
        "новый": ("🔔 НОВЫЙ", CORAL_BTN), "принят": ("⏳ Сборка", BRAND_BLUE),
        "поиск_курьера": ("🔍 Поиск", "#D97706"), "передан_курьеру": ("📦 У курьера", PURPLE),
        "в_доставке": ("🛵 В пути", GREEN), "доставлен": ("✅ Доставлен", GREEN), "отклонен": ("❌ Отменён", RED_ALERT),
    }
    txt, col = mapping.get(st, (st, MUTED))
    return ft.Container(bgcolor=col, padding=5, border_radius=8, content=ft.Text(txt, size=11, color=WHITE))

def get_order_by_id(oid):
    for o in db["orders_list"]:
        if o["id"] == oid:
            return o
    return None

def main(page):
    page.title = "MD — Морские Деликатесы"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 445
    page.window.height = 865
    page.bgcolor = SEA_BG
    page.padding = 0

    page.meta = {
        "viewport": "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no",
        "theme-color": "#0F4C64",
        "apple-mobile-web-app-capable": "yes",
        "apple-mobile-web-app-status-bar-style": "black-translucent",
        "apple-mobile-web-app-title": "MD"
    }

    auth_error_text = ft.Text("", size=12, color=RED_ALERT)
    login_name_input = white_field(label_txt="Имя и Фамилия", hint="Дмитрий Жаров")
    login_phone_input = white_field(label_txt="Номер телефона", hint="+79950057432")
    login_pass_input = white_field(label_txt="Пароль", hint="Введите пароль")
    login_pass_input.password = True
    login_pass_input.can_reveal_password = True

    root = ft.Column(spacing=0)
    main_screen = ft.Container(bgcolor=SEA_BG, width=445, height=845, content=root)
    page.add(main_screen)

    install_dlg = ft.AlertDialog(
        title=ft.Text("📱 Установка приложения MD"),
        content=ft.Column([
            ft.Text("Чтобы приложение работало как нативная программа:", size=13, color=BLACK),
            ft.Text("1. В браузере (Chrome / Safari) нажмите на меню (три точки ⋮).", size=12, color=MUTED),
            ft.Text("2. Выберите пункт «На главный экран» или «Установить приложение».", size=12, color=MUTED),
        ], spacing=8, tight=True),
        actions=[ft.TextButton("Понятно", on_click=lambda e: page.close(install_dlg))]
    )

    def trigger_install(e):
        page.open(install_dlg)

    def login_user(e):
        name = login_name_input.value.strip()
        phone = login_phone_input.value.strip()
        pwd = login_pass_input.value.strip()
        if not name or not phone or not pwd:
            auth_error_text.value = "⚠️ Заполните все поля!"
            render()
            return
        
        users = load_users_from_db()
        matched = None
        for u in users:
            if u["name"].lower() == name.lower() and u["phone"] == phone:
                if u["password"] == pwd or (phone == "+79950057432" and pwd == "12345"):
                    matched = u
                    break
        if matched:
            db["fio"] = matched["name"]
            db["phone"] = matched["phone"]
            db["role"] = matched["role"]
            render()
        else:
            auth_error_text.value = "❌ Неверные данные или пароль!"
            render()

    def render_owner_view(body_col):
        stores_list = load_stores_from_db()
        users_list = load_users_from_db()
        
        header = ft.Container(
            bgcolor=BRAND_DARK, padding=12, border_radius=16,
            content=ft.Column([
                ft.Row([
                    ft.Row([logo(28), ft.Text("ПАНЕЛЬ ВЛАДЕЛЬЦА", size=14, color=WHITE)], spacing=8),
                    ft.Container(
                        bgcolor=CORAL_BTN, padding=6, border_radius=8,
                        on_click=lambda e: (db.update({"role": "Покупатель", "tab": "Профиль"}), render()),
                        content=ft.Row([ft.Text("👤", size=14), ft.Text("Профиль", size=11, color=WHITE)], spacing=4)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"Магазинов: {len(stores_list)} | Пользователей: {len(users_list)}", size=11, color=SEA_BG)
            ], spacing=6)
        )
        body_col.controls.append(header)
        
        owner_tabs = ["Каталог", "Новости", "Люди", "Магазины", "Заказы"]
        current_o_tab = db.get("owner_tab", "Каталог")
        
        tabs_row = ft.Row([
            ft.Container(
                bgcolor=BRAND_DARK if current_o_tab == t else WHITE,
                padding=10, border_radius=12, width=74,
                on_click=lambda e, tab=t: (db.update({"owner_tab": tab}), render()),
                content=ft.Text(t, size=11, color=WHITE if current_o_tab == t else BLACK, text_align=ft.TextAlign.CENTER)
            ) for t in owner_tabs
        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER)
        body_col.controls.append(tabs_row)

        if current_o_tab == "Каталог":
            tg_input = white_field(val=db["tg_channel"], hint="morskie_delikatesy")
            def save_tg(e):
                cleaned = clean_tg_link(tg_input.value)
                db["tg_channel"] = cleaned
                save_db_setting("tg_channel", cleaned)
                render()

            body_col.controls.append(
                ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Column([
                    ft.Text("📢 Telegram-канал новостей", size=13, color=BLACK),
                    tg_input,
                    ft.Container(bgcolor=BRAND_BLUE, padding=8, border_radius=10, on_click=save_tg, content=ft.Text("💾 Сохранить канал", size=11, color=WHITE, text_align=ft.TextAlign.CENTER))
                ], spacing=8))
            )
            
            body_col.controls.append(sea_divider("Управление каталогом и акциями"))
            for pname, pdata in PRODUCTS.items():
                p_card = ft.Container(
                    bgcolor=WHITE, padding=12, border_radius=14,
                    content=ft.Row([
                        ft.Row([ft.Text(pdata['icon'], size=24), ft.Column([ft.Text(pname, size=13, color=BLACK), ft.Text(f"Цена: {pdata['price']} ₽", size=11, color=MUTED)], spacing=2)], spacing=10),
                        ft.Container(
                            bgcolor=BRAND_BLUE, padding=8, border_radius=10,
                            on_click=lambda e, name=pname: (PRODUCTS[name].update({"is_promo": not PRODUCTS[name]["is_promo"]}), render()),
                            content=ft.Text("🔥 Акция" if not pdata['is_promo'] else "✓ Активен", size=11, color=WHITE)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
                body_col.controls.append(p_card)
        elif current_o_tab == "Люди":
            body_col.controls.append(sea_divider("Список пользователей"))
            for u in users_list:
                body_col.controls.append(
                    ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Row([
                        ft.Column([ft.Text(u["name"], size=13, color=BLACK), ft.Text(f"{u['phone']} • {u['role']}", size=11, color=MUTED)], spacing=2),
                        ft.Container(bgcolor=CORAL_BTN, padding=6, border_radius=8, on_click=lambda e, uid=u["id"]: (delete_user_from_db(uid), render()), content=ft.Text("🗑", size=12, color=WHITE))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                )
        elif current_o_tab == "Магазины":
            body_col.controls.append(sea_divider("Торговые точки"))
            for s in stores_list:
                body_col.controls.append(
                    ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Row([
                        ft.Column([ft.Text(s["name"], size=13, color=BLACK), ft.Text(s["address"], size=11, color=MUTED)], spacing=2),
                        ft.Container(bgcolor=CORAL_BTN, padding=6, border_radius=8, on_click=lambda e, sid=s["id"]: (delete_store_from_db(sid), render()), content=ft.Text("🗑", size=12, color=WHITE))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                )
        elif current_o_tab in ["Новости", "Заказы"]:
            body_col.controls.append(sea_divider(f"Раздел: {current_o_tab}"))
            body_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=14, content=ft.Text("Информация обновляется в реальном времени.", size=12, color=BLACK)))

    def render():
        root.controls.clear()
        
        if not db.get("fio") or not db.get("phone"):
            auth_col = ft.Column([
                ft.Container(height=30),
                logo(60),
                ft.Text("🦐 MD • ДЕЛИКАТЕСЫ", size=22, color=BRAND_DARK),
                auth_error_text,
                login_name_input,
                login_phone_input,
                login_pass_input,
                ft.Container(height=10),
                ft.Container(bgcolor=BRAND_BLUE, padding=12, border_radius=14, width=380, on_click=login_user, content=ft.Text("🔑 Войти в аккаунт", size=14, color=WHITE, text_align=ft.TextAlign.CENTER))
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            root.controls.append(ft.Container(bgcolor=WHITE, padding=15, border_radius=20, width=425, height=820, content=auth_col))
            page.update()
            return

        body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        if db["role"] == "Владелец":
            root.controls.append(body)
            render_owner_view(body)
            page.update()
            return

        body.controls.append(
            ft.Container(bgcolor=WHITE, padding=20, border_radius=16, content=ft.Column([
                ft.Text(f"👤 Добро пожаловать, {db['fio']}!", size=16, color=BLACK),
                ft.Text(f"👑 Роль: {db['role']}", size=13, color=BRAND_BLUE),
                ft.Container(
                    bgcolor=BRAND_BLUE, padding=12, border_radius=14, on_click=trigger_install,
                    content=ft.Text("📱 Установить приложение на телефон", size=13, color=WHITE, text_align=ft.TextAlign.CENTER)
                ),
                ft.Container(
                    bgcolor=RED_ALERT, padding=12, border_radius=14, on_click=lambda e: (db.update({"fio": "", "phone": ""}), render()),
                    content=ft.Text("🚪 Выйти из аккаунта", size=13, color=WHITE, text_align=ft.TextAlign.CENTER)
                )
            ], spacing=12))
        )
        root.controls.append(body)
        page.update()

    render()

if __name__ == "__main__":
    ft.app(
        target=main, 
        view=ft.AppView.WEB_BROWSER, 
        port=int(os.environ.get("PORT", 8550)), 
        host="0.0.0.0",
        assets_dir="."
    )
