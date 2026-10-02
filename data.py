import os
import re
import sqlite3
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

COURIER_RATE = 150

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

def strike_price(val):
    s = f"{val}.00"
    return "".join(ch + "\u0336" for ch in s) + " ₽"

def get_promo_names():
    return [k for k, v in PRODUCTS.items() if v.get("is_promo", False)]

DB_NAME = "market.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            role TEXT,
            deliveries INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            address TEXT,
            hours TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE phone = '+79950057432'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (name, phone, role, deliveries) VALUES (?, ?, ?, ?)", 
                       ("Дмитрий Жаров", "+79950057432", "Владелец", 0))
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
    cursor.execute("SELECT id, name, phone, role, deliveries FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "phone": r[2], "role": r[3], "deliveries": r[4]} for r in rows]

def save_user_to_db(name, phone, role="Покупатель"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, phone, role, deliveries) VALUES (?, ?, ?, 0)", (name, phone, role))
    conn.commit()
    conn.close()

def update_user_role_in_db(uid, new_role):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, uid))
    conn.commit()
    conn.close()

def delete_user_from_db(uid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

def load_stores_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, address, hours FROM stores")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "address": r[2], "hours": r[3]} for r in rows]

def save_store_to_db(name, address, hours="08:00 – 22:00"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stores (name, address, hours) VALUES (?, ?, ?)", (name, address, hours))
    conn.commit()
    conn.close()

def delete_store_from_db(sid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stores WHERE id = ?", (sid,))
    conn.commit()
    conn.close()


db = {
    "role": "Владелец",
    "tab": "Главная",
    "subscreen": None,
    "search_q": "",
    "fio": "Дмитрий Жаров",
    "phone": "+79950057432",
    "address": "Волховская улица, 8",
    "intercom": "Подъезд 2, кв. 45, домофон 45К1234",
    "time_slot": None,
    "slot_warning": False,
    "orders": 9,
    "status": "Золото",
    "bonuses": 2500,
    "spend_bonuses": False,
    "pay_methods": ["⚡ СБП (Система быстрых платежей)", "🟢 SberPay", "🟡 Т-Pay", "💳 Карта МИР •••• 6148"],
    "selected_pay": "⚡ СБП (Система быстрых платежей)",
    "cart": {"Креветки королевские": 1, "Минтай Borealis филе": 1},
    "gift_added": False,
    "promo_discount": 0,
    "comment": "Позвонить, если нужна замена",

    "categories": ["Морепродукты и рыба", "Напитки и вода", "К столу и десерты"],

    "owner_tab": "Каталог",
    "owner_cat_filter": "Все",
    "owner_search": "",
    "owner_edit_target": None,

    "tg_channel": get_db_setting("tg_channel", "morskie_delikatesy"),
    "tg_auto_sync": True,
    "playing_video_id": None,
    "news_posts": [
        {
            "id": 1, "author": "📲 Telegram-канал @morskie_delikatesy",
            "date": "Сегодня • Акция из Telegram",
            "text": "РЕЦЕПТ ГОТОВ 😋😋😋\nМидии, как в ресторане, только МНОГО И ВСЕГО ЗА 249₽! 🔥🔥🔥\nПотому что на мидии чилийские в 2 створках акция 🔥🔥🔥 Скидка прям огонь: всего 249Р/0,5КГ вместо 390Р!! 🤤",
            "photo": "logo.jpg", "video": "Видео-рецепт приготовления мидий (00:45)", "is_tg": True
        }
    ],

    "active_store_name": "Морские Деликатесы №1 (Северная)",
    "active_courier_name": "Алексей Ветров",

    "store_tab": "Заказы",
    "store_prof_filter": "Отправленные",
    "store_active_id": None,
    "store_mode": "detail",
    "store_reject_err": False,

    "courier_tab": "Доставки",
    "courier_active_id": None,
    "courier_mode": "detail",
    "courier_reject_err": False,
    "courier_cancelled_log": [],

    "owner_store_filter": "Все",
    "owner_order_id": None,
    "client_chat_id": None,

    "orders_list": [
        {
            "id": 106, "store": "Морские Деликатесы №1 (Северная)", "courier": "Не назначен",
            "fio": "Анна Морская", "phone": "+7 (918) 555-12-90", "client_status": "Золото (Кешбэк 10%)",
            "address": "ул. 1-го Мая, 580/3", "intercom": "Подъезд 1, кв. 12, домофон 12#",
            "slot": "⚡ Заказать сейчас (25 мин)", "pay_method": "🟢 SberPay",
            "items": {"Форель слабосолёная": 2, "Чиабатта пшеничная": 1},
            "pack_fee": 49, "discount": 133, "total": 1194, "gift": True,
            "comment": "Домофон работает", "state": "новый", "reject_reason": "",
            "chat": ["Покупатель: Жду экспресс-доставку!"]
        }
    ]
}

def sync_telegram_channel():
    raw_input_ch = db["tg_channel"]
    clean_ch = raw_input_ch.replace("https://t.me/", "").replace("http://t.me/", "").replace("@", "").strip().split("/")[0]
    if not clean_ch:
        clean_ch = "morskie_delikatesy"

    db["tg_channel"] = clean_ch
    save_db_setting("tg_channel", clean_ch)

    fetched = 0
    try:
        req = urllib.request.Request(f"https://t.me/s/{clean_ch}", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        html = urllib.request.urlopen(req, timeout=5).read().decode("utf-8", errors="ignore")
        
        # Разбиваем страницу на блоки отдельных сообщений Telegram
        messages = html.split('tgme_widget_message_wrap')
        for msg in messages[1:]:
            # Извлекаем текст поста
            t_match = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', msg, re.S)
            if not t_match:
                continue
            clean_t = re.sub(r"<[^>]+>", "", t_match.group(1)).strip()
            if not clean_t:
                continue

            # Ищем ссылку на фото в посте (background-image)
            photo_url = "logo.jpg"
            img_match = re.search(r'background-image:\s*url\(\'([^\']+)\'\)', msg)
            if img_match:
                photo_url = img_match.group(1)

            # Проверяем наличие видео / медиа-проигрывателя в сообщении
            video_desc = ""
            if "tgme_widget_message_video" in msg or "tgme_widget_message_roundvideo" in msg or "playing" in msg:
                video_desc = f"Видео-материал из @{clean_ch} (00:45)"

            # Добавляем в ленту, если такого поста еще нет
            if not any(p["text"] == clean_t for p in db["news_posts"]):
                new_id = max([p["id"] for p in db["news_posts"]], default=0) + 1
                db["news_posts"].insert(0, {
                    "id": new_id, 
                    "author": f"📲 Telegram @{clean_ch}",
                    "date": "Синхронизировано из Telegram",
                    "text": clean_t[:500], 
                    "photo": photo_url,
                    "video": video_desc, 
                    "is_tg": True
                })
                fetched += 1
    except Exception:
        pass
    
    # Если внешняя сеть заблокирована или посты не найдены, добавляем демонстрационный пост с фото
    if fetched == 0 and not any("Мидии, как в ресторане" in p["text"] for p in db["news_posts"]):
        new_id = max([p["id"] for p in db["news_posts"]], default=0) + 1
        db["news_posts"].insert(0, {
            "id": new_id, 
            "author": f"📲 Telegram-канал @{clean_ch}",
            "date": "Акция из Telegram",
            "text": "РЕЦЕПТ ГОТОВ 😋😋😋\nМидии, как в ресторане, только МНОГО И ВСЕГО ЗА 249₽! 🔥🔥🔥\nПотому что на мидии чилийские в 2 створках акция 🔥🔥🔥 Скидка прям огонь: всего 249Р/0,5КГ вместо 390Р!! 🤤",
            "photo": "logo.jpg", 
            "video": "Видео-рецепт приготовления мидий (00:45)", 
            "is_tg": True
        })

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
        "новый": ("🔔 НОВЫЙ", CORAL_BTN),
        "принят": ("⏳ Сборка", BRAND_BLUE),
        "поиск_курьера": ("🔍 Поиск курьера", "#D97706"),
        "передан_курьеру": ("📦 У курьера", PURPLE),
        "в_доставке": ("🛵 В пути (GPS)", GREEN),
        "доставлен": ("✅ Доставлен", GREEN),
        "отклонен": ("❌ Отменён", RED_ALERT),
    }
    txt, col = mapping.get(st, (st, MUTED))
    return ft.Container(bgcolor=col, padding=5, border_radius=8, content=ft.Text(txt, size=11, color=WHITE))

def get_order_by_id(oid):
    for o in db["orders_list"]:
        if o["id"] == oid:
            return o
    return None
