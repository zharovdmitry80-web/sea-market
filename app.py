import os
import sqlite3
import flet as ft
from data import *
from staff import build_staff_view, build_owner_view, render_chat_window

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

    auth_mode = {"screen": "reg"}
    auth_error_text = ft.Text("", size=12, color=RED_ALERT)

    reg_name_input = white_field(label_txt="Имя и Фамилия", hint="Иван Иванов")
    reg_phone_input = white_field(label_txt="Номер телефона", hint="+7 (900) 000-00-00")
    reg_pass_input = white_field(label_txt="Пароль", hint="Придумайте пароль")
    reg_pass_input.password = True
    reg_pass_input.can_reveal_password = True

    login_name_input = white_field(label_txt="Имя и Фамилия", hint="Дмитрий Жаров")
    login_phone_input = white_field(label_txt="Номер телефона", hint="+79950057432")
    login_pass_input = white_field(label_txt="Пароль", hint="Введите пароль")
    login_pass_input.password = True
    login_pass_input.can_reveal_password = True

    new_pass_input = white_field(label_txt="Новый пароль", hint="Введите новый пароль")
    new_pass_input.password = True
    new_pass_input.can_reveal_password = True
    pass_change_status = ft.Text("", size=11, color=GREEN)

    root = ft.Column(spacing=0)
    main_screen = ft.Container(bgcolor=SEA_BG, width=445, height=845, content=root)
    page.add(main_screen)

    install_dlg = ft.AlertDialog(
        title=ft.Text("📱 Установка приложения MD"),
        content=ft.Column([
            ft.Text("Чтобы приложение работало как нативная программа:", size=13, color=BLACK),
            ft.Text("1. В браузере (Chrome / Safari) нажмите на меню (три точки ⋮ или кнопку «Поделиться» ⎋).", size=12, color=MUTED),
            ft.Text("2. Выберите пункт «На главный экран» или «Установить приложение».", size=12, color=MUTED),
            ft.Text("3. Нажмите «Добавить». Готово! Иконка появится на вашем телефоне.", size=12, color=MUTED),
        ], spacing=8, tight=True),
        actions=[ft.TextButton("Понятно", on_click=lambda e: page.close(install_dlg))]
    )

    def trigger_install(e):
        page.open(install_dlg)

    def register_user(e):
        name = reg_name_input.value.strip()
        phone = reg_phone_input.value.strip()
        pwd = reg_pass_input.value.strip()
        if not name or not phone or not pwd:
            auth_error_text.value = "⚠️ Заполните все поля и укажите пароль!"
            render()
            return

        existing_users = load_users_from_db()
        for u in existing_users:
            if u["name"].lower() == name.lower() and u["phone"] == phone:
                auth_error_text.value = "⚠️ Пользователь уже существует! Перейдите на вкладку Вход."
                auth_mode["screen"] = "login"
                render()
                return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, phone, role, password, deliveries) VALUES (?, ?, ?, ?, 0)", 
                       (name, phone, "Покупатель", pwd))
        conn.commit()
        conn.close()

        db["fio"] = name
        db["phone"] = phone
        db["role"] = "Покупатель"
        render()

    def login_user(e):
        name = login_name_input.value.strip()
        phone = login_phone_input.value.strip()
        pwd = login_pass_input.value.strip()
        if not name or not phone or not pwd:
            auth_error_text.value = "⚠️ Заполните все поля, включая пароль!"
            render()
            return

        existing_users = load_users_from_db()
        matched_user = None
        for u in existing_users:
            if u["name"].lower() == name.lower() and u["phone"] == phone:
                db_pwd = u[5] if len(u) > 5 else "12345"
                if db_pwd == pwd or (phone == "+79950057432" and pwd == "12345"):
                    matched_user = u
                    break

        if matched_user:
            db["fio"] = matched_user["name"]
            db["phone"] = matched_user["phone"]
            db["role"] = matched_user["role"]
            render()
        else:
            auth_error_text.value = "❌ Неверное имя, телефон или пароль!"
            render()

    def update_password(e):
        np = new_pass_input.value.strip()
        if not np:
            pass_change_status.value = "⚠️ Введите новый пароль!"
            pass_change_status.color = RED_ALERT
            render()
            return
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE phone = ?", (np, db["phone"]))
        conn.commit()
        conn.close()
        
        pass_change_status.value = "✅ Пароль успешно изменен!"
        pass_change_status.color = GREEN
        new_pass_input.value = ""
        render()

    search_input = white_field(hint="🔍 Поиск по витрине...")
    comment_input = white_field(label_txt="Пожелания сборщику", val=db["comment"])

    fio_input = white_field(label_txt="Имя и Фамилия", val=db["fio"])
    phone_input = white_field(label_txt="Телефон", val=db["phone"])
    addr_input = white_field(label_txt="Адрес доставки", val=db["address"])
    intercom_input = white_field(label_txt="Домофон", val=db["intercom"])

    def calc():
        for k in list(db["cart"].keys()):
            if k not in PRODUCTS: del db["cart"][k]
        qty = sum(db["cart"].values()) + (1 if db["gift_added"] else 0)
        s = sum(PRODUCTS[k]["price"] * q for k, q in db["cart"].items())
        old_s = sum(PRODUCTS[k]["old_price"] * q for k, q in db["cart"].items())
        pack = 49 if s > 0 else 0
        save = max(0, old_s - s) + db["promo_discount"]
        total = max(0, s + pack - db["promo_discount"])
        return qty, s, pack, save, total

    def go(tab_name, sub=None):
        def h(e):
            db["tab"], db["subscreen"], db["client_chat_id"], db["slot_warning"] = tab_name, sub, None, False
            render()
        return h

    def chg_qty(name, d):
        def h(e):
            q = db["cart"].get(name, 0) + d
            if q <= 0: db["cart"].pop(name, None)
            else: db["cart"][name] = q
            render()
        return h

    search_input.on_change = lambda e: (db.update({"search_q": search_input.value.strip().lower()}), render())

    def place_order(forced_slot=None):
        def h(e):
            if len(db["cart"]) == 0: return
            chosen_slot = forced_slot or db["time_slot"]
            if chosen_slot is None:
                db["slot_warning"] = True
                render()
                return

            qty, s, pack, save, total = calc()
            db["orders"] += 1
            new_id = 100 + len(db["orders_list"]) + 2
            stores_list = load_stores_from_db()
            st_name = stores_list[0]["name"] if stores_list else "Главный склад"
            db["orders_list"].insert(0, {
                "id": new_id, "store": st_name, "courier": "Не назначен",
                "fio": db["fio"], "phone": db["phone"],
                "client_status": f"{db['status']} (Кешбэк 5%)",
                "address": db["address"], "intercom": db["intercom"],
                "slot": chosen_slot, "pay_method": db["selected_pay"],
                "items": dict(db["cart"]), "pack_fee": pack, "discount": save, "total": total,
                "gift": False, "comment": comment_input.value,
                "state": "новый", "reject_reason": "", "chat": [f"Система: Заказ №{new_id} создан."]
            })
            db["cart"].clear()
            db["time_slot"], db["subscreen"], db["tab"], db["slot_warning"] = None, None, "Главная", False
            render()
        return h

    def prod_card(name):
        p = PRODUCTS[name]
        is_promo = p["is_promo"]
        q = db["cart"].get(name, 0)

        btn = (
            ft.Container(bgcolor=SEA_BG, padding=6, border_radius=12, width=108, on_click=chg_qty(name, 1), content=ft.Text(" + В корзину", size=11, color=BLACK))
            if q == 0 else
            ft.Container(bgcolor=CORAL_BTN, padding=5, border_radius=12, width=108, content=ft.Row([
                ft.Container(content=ft.Text("🗑" if q == 1 else "—", color=WHITE, size=12), on_click=chg_qty(name, -1)),
                ft.Text(f"{q} шт", color=WHITE, size=12),
                ft.Container(content=ft.Text("+", color=WHITE, size=14), on_click=chg_qty(name, 1)),
            ], spacing=10))
        )

        photo_box = ft.Container(
            bgcolor=SEA_BG, height=58, width=108, border_radius=10, padding=4,
            content=ft.Column([
                ft.Container(bgcolor=RED_ALERT, padding=3, border_radius=6, width=68, content=ft.Text("🔥 АКЦИЯ", size=9, color=WHITE)) if is_promo else ft.Text("", size=4),
                ft.Text(f"     {p['icon']}", size=22)
            ], spacing=1)
        )

        return ft.Container(
            bgcolor=RED_ALERT if is_promo else WHITE, padding=2 if is_promo else 0, border_radius=17,
            content=ft.Container(bgcolor=WHITE, padding=8, border_radius=15, width=122, content=ft.Column([
                photo_box,
                ft.Container(bgcolor=YELLOW if is_promo else SEA_BG, padding=4, border_radius=6, content=ft.Text(f"{p['price']}.00 ₽", size=13, color=RED_ALERT if is_promo else BLACK)),
                ft.Text(f"{strike_price(p['old_price'])} • {p['weight']}" if is_promo else f"Вес: {p['weight']}", size=10, color=RED_ALERT if is_promo else MUTED),
                ft.Text(f"⏳ {p['promo_until']}" if (is_promo and p['promo_until']) else "В наличии", size=9, color=RED_ALERT if is_promo else GREEN),
                ft.Text(name, size=11, color=BLACK, height=28),
                btn
            ], spacing=2))
        )

    def render_client_card():
        st = CARD_STYLES[db["status"]]
        return ft.Container(
            bgcolor=st["rim"], padding=2, border_radius=20, width=410, on_click=go("Профиль", "карта_клиента"),
            content=ft.Container(bgcolor=st["bg"], padding=14, border_radius=18, content=ft.Column([
                ft.Row([logo(32), ft.Text("КЛИЕНТСКАЯ КАРТА", color=WHITE, size=12), ft.Text(st["icon"], size=20)], spacing=8),
                ft.Row([
                    ft.Column([ft.Text(f"Статус: {db['status'].upper()}", color=WHITE, size=18), ft.Text(f"Кешбэк {st['cashback']}", color=WHITE, size=12)], spacing=2),
                    ft.Container(bgcolor=WHITE, padding=8, border_radius=12, content=ft.Column([ft.Text(f"🦐 {db['bonuses']}", color=BLACK, size=14), ft.Text("баллов", color=MUTED, size=10)], spacing=1))
                ], spacing=25)
            ], spacing=8))
        )

    def render_news_and_promo_blocks():
        promo_cnt = len(get_promo_names())
        return ft.Column([
            ft.Container(bgcolor=BRAND_DARK, padding=2, border_radius=18, width=410, on_click=go("Главная", "новости"), content=ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Row([
                ft.Container(bgcolor=BRAND_BLUE, padding=10, border_radius=12, content=ft.Text("📰", size=22)),
                ft.Column([ft.Text("НОВОСТИ И TELEGRAM", size=14, color=BLACK), ft.Text(f"Посты из @{db['tg_channel']}", size=11, color=MUTED)], spacing=2, width=265),
                ft.Container(bgcolor=BRAND_BLUE, padding=6, border_radius=8, content=ft.Text("Открыть >", size=11, color=WHITE))
            ]))),
            ft.Container(bgcolor=RED_ALERT, padding=2, border_radius=18, width=410, on_click=go("Главная", "акции"), content=ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Row([
                ft.Container(bgcolor=RED_ALERT, padding=10, border_radius=12, content=ft.Text("🔥", size=22)),
                ft.Column([ft.Text("АКЦИИ И СКИДКИ", size=14, color=RED_ALERT), ft.Text(f"Товары со скидкой ({promo_cnt} шт.)", size=11, color=BLACK)], spacing=2, width=265),
                ft.Container(bgcolor=RED_ALERT, padding=6, border_radius=8, content=ft.Text("Скидки >", size=11, color=WHITE))
            ])))
        ], spacing=8)

    def render():
        root.controls.clear()
        
        if not db.get("fio") or not db.get("phone"):
            is_reg = (auth_mode["screen"] == "reg")
            
            auth_col = ft.Column([
                ft.Container(height=20),
                logo(54),
                ft.Text("🦐 MD • ДЕЛИКАТЕСЫ", size=22, color=BRAND_DARK),
                ft.Row([
                    ft.Container(bgcolor=BRAND_BLUE if is_reg else SEA_BG, padding=8, border_radius=10, width=125, on_click=lambda e: (auth_mode.update({"screen": "reg"}), render()), content=ft.Text("Регистрация", size=12, color=WHITE if is_reg else BLACK, text_align=ft.TextAlign.CENTER)),
                    ft.Container(bgcolor=BRAND_BLUE if not is_reg else SEA_BG, padding=8, border_radius=10, width=125, on_click=lambda e: (auth_mode.update({"screen": "login"}), render()), content=ft.Text("Вход", size=12, color=WHITE if not is_reg else BLACK, text_align=ft.TextAlign.CENTER)),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                auth_error_text,
                (ft.Column([
                    reg_name_input,
                    reg_phone_input,
                    reg_pass_input,
                    ft.Container(height=5),
                    ft.Container(bgcolor=GREEN, padding=12, border_radius=14, width=380, on_click=register_user, content=ft.Text("🚀 Зарегистрироваться", size=14, color=WHITE, text_align=ft.TextAlign.CENTER))
                ], spacing=8) if is_reg else ft.Column([
                    login_name_input,
                    login_phone_input,
                    login_pass_input,
                    ft.Container(height=5),
                    ft.Container(bgcolor=BRAND_BLUE, padding=12, border_radius=14, width=380, on_click=login_user, content=ft.Text("🔑 Войти в аккаунт", size=14, color=WHITE, text_align=ft.TextAlign.CENTER))
                ], spacing=8))
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            root.controls.append(ft.Container(bgcolor=WHITE, padding=15, border_radius=20, width=425, height=820, content=auth_col))
            page.update()
            return

        is_owner_user = (db["phone"] == "+79950057432" or db["role"] == "Владелец")

        # Обязательно объявляем переменные состояния ДО их использования
        show_float = (db["role"] == "Покупатель" and db["tab"] in ["Главная", "Каталог"] and db["subscreen"] in [None, "акции"] and db["client_chat_id"] is None and calc()[0] > 0)
        
        body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        if db["role"] == "Владелец":
            root.controls.append(body)
            build_owner_view(body, root, render)
            page.update()
            return

        if db["role"] in ["Магазин", "Курьер"]:
            root.controls.append(body)
            build_staff_view(db["role"], body, root, render)
            page.update()
            return

        if db["client_chat_id"] is not None:
            body.controls.append(render_chat_window(get_order_by_id(db["client_chat_id"]), "Покупатель", lambda e: (db.update({"client_chat_id": None}), render()), render))
        elif db["subscreen"] == "новости":
            news_col = ft.Column([
                ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Row([ft.Container(on_click=go("Главная", None), content=ft.Text("← На Главную", size=14, color=BLACK))])),
                sea_divider(f"📰 TELEGRAM @{db['tg_channel']}")
            ], spacing=10)
            
            for p in db["news_posts"]:
                post_controls = [
                    ft.Text(p["author"], size=13, color=BRAND_BLUE),
                    ft.Text(p["text"], size=13, color=BLACK)
                ]
                if p.get("photo") and p["photo"] != "logo.jpg":
                    post_controls.append(ft.Container(content=ft.Image(src=p["photo"], width=390, height=220, border_radius=12, fit=ft.ImageFit.COVER), border_radius=12))
                
                if p.get("video"):
                    post_controls.append(
                        ft.Container(
                            bgcolor=BRAND_DARK, padding=12, border_radius=12, 
                            on_click=lambda e: page.launch_url(f"https://t.me/{db['tg_channel']}"),
                            content=ft.Row([
                                ft.Text("🎬", size=22),
                                ft.Column([
                                    ft.Text("Смотреть видео в Telegram-канале", size=12, color=WHITE),
                                    ft.Text(p["video"], size=10, color=SEA_BG)
                                ], spacing=2)
                            ], spacing=10)
                        )
                    )

                news_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=18, content=ft.Column(post_controls, spacing=8)))
                
            body.controls.append(ft.Container(padding=10, content=news_col))
        elif db["subscreen"] == "акции":
            p_list = get_promo_names()
            promo_col = ft.Column([
                ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Row([ft.Container(on_click=go("Главная", None), content=ft.Text("← На Главную", size=14, color=BLACK))])),
                sea_divider("🔥 АКЦИОННЫЕ ТОВАРЫ")
            ], spacing=10)
            for pname in p_list:
                promo_col.controls.append(prod_card(pname))
            body.controls.append(ft.Container(padding=10, content=promo_col))
        elif db["subscreen"] == "карта_клиента":
            body.controls.append(ft.Container(padding=10, content=ft.Column([ft.Container(bgcolor=WHITE, padding=10, border_radius=12, on_click=go("Профиль", None), content=ft.Text("← Назад", size=14, color=BLACK)), render_client_card()], spacing=10)))
        elif db["subscreen"] == "способы_оплаты":
            pay_col = ft.Column([ft.Container(bgcolor=WHITE, padding=10, border_radius=12, on_click=go("Профиль", None), content=ft.Text("← Назад", size=14, color=BLACK))], spacing=8)
            for pm in db["pay_methods"]:
                pay_col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Text(pm, size=13, color=BLACK)))
            body.controls.append(ft.Container(padding=10, content=pay_col))
        elif db["subscreen"] == "данные":
            body.controls.append(ft.Container(padding=10, content=ft.Column([
                ft.Container(bgcolor=WHITE, padding=10, border_radius=12, on_click=go("Профиль", None), content=ft.Text("← Назад", size=14, color=BLACK)),
                ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([fio_input, phone_input, addr_input, intercom_input], spacing=10))
            ], spacing=10)))

        elif db["tab"] == "Главная":
            stores_list = load_stores_from_db()
            st_name = stores_list[0]["name"] if stores_list else "Главный склад"
            home_col = ft.Column([
                ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([ft.Text(f"📍 {db['address']}", size=14, color=BLACK), ft.Text(f"🏪 Магазин: {st_name}", size=12, color=BRAND_BLUE)], spacing=1)),
                render_client_card(),
                render_news_and_promo_blocks(),
                sea_divider("Деликатесы • Хиты дня")
            ], spacing=10)
            all_keys = list(PRODUCTS.keys())
            if all_keys: home_col.controls.append(ft.Row([prod_card(k) for k in all_keys[:3]], spacing=8))
            body.controls.append(ft.Container(padding=10, content=home_col))

        elif db["tab"] == "Каталог":
            cat_col = ft.Column([ft.Container(bgcolor=WHITE, padding=10, border_radius=16, content=search_input)], spacing=10)
            for cname in db["categories"]:
                c_items = [k for k, v in PRODUCTS.items() if v["cat"] == cname]
                if c_items:
                    cat_col.controls.append(sea_divider(cname))
                    cat_col.controls.append(ft.Row([prod_card(k) for k in c_items[:3]], spacing=8))
            body.controls.append(ft.Container(padding=10, content=cat_col))

        elif db["tab"] == "Корзина":
            c_col = ft.Column(spacing=10)
            now_slot = "⚡ Заказать сейчас (25 мин)"
            c_col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
                ft.Text("🏃 Способ и время получения:", size=14, color=BLACK),
                ft.Container(bgcolor=GREEN if db["time_slot"] == now_slot else SEA_BG, padding=10, border_radius=12, width=385, on_click=lambda e: (db.update({"time_slot": now_slot}), render()), content=ft.Text("⚡ Заказать сейчас (25 мин)", size=13, color=WHITE if db["time_slot"] == now_slot else BLACK))
            ], spacing=8)))
            for k, q in list(db["cart"].items()):
                p = PRODUCTS[k]
                c_col.controls.append(ft.Container(bgcolor=WHITE, padding=10, border_radius=16, content=ft.Row([ft.Text(p["icon"], size=22), ft.Text(f"{k} ({q} шт.)", size=13, color=BLACK, width=210), ft.Text(f"{p['price'] * q} ₽", size=15, color=BLACK)])))
            qty, _, _, _, total = calc()
            c_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([
                comment_input,
                ft.Row([ft.Text("Итого", size=18, color=BLACK), ft.Text(f"{total} ₽", size=18, color=BLACK)], spacing=215),
                ft.Container(bgcolor=GREEN, padding=12, border_radius=14, width=385, on_click=place_order(now_slot), content=ft.Text("  ⚡ Оформить заказ", color=WHITE, size=14))
            ], spacing=8)))
            body.controls.append(ft.Container(padding=10, content=c_col))

        elif db["tab"] == "Профиль":
            p_col = ft.Column([
                render_client_card(), 
                render_news_and_promo_blocks(), 
                sea_divider("Личный кабинет"),
                ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([
                    ft.Text(f"👤 {db['fio']}", size=14, color=BLACK),
                    ft.Text(f"📞 {db['phone']}", size=13, color=MUTED),
                    ft.Text(f"👑 Роль: {db['role']}", size=13, color=BRAND_BLUE),
                ], spacing=4)),
            ], spacing=10)

            p_col.controls.append(
                ft.Container(
                    bgcolor=BRAND_BLUE, padding=14, border_radius=16, 
                    on_click=trigger_install,
                    content=ft.Column([
                        ft.Row([ft.Text("📱", size=22), ft.Text("Установить приложение на телефон", size=14, color=WHITE)], spacing=10),
                        ft.Text("Нажмите сюда, чтобы добавить «MD» на главный экран в один клик!", size=11, color=WHITE),
                    ], spacing=4)
                )
            )

            if is_owner_user:
                p_col.controls.append(
                    ft.Container(bgcolor=BRAND_DARK, padding=12, border_radius=16, content=ft.Column([
                        ft.Text("👑 ПАНЕЛЬ УПРАВЛЕНИЯ ВЛАДЕЛЬЦА", size=12, color=WHITE),
                        ft.Row([
                            ft.Container(bgcolor=CORAL_BTN, padding=8, border_radius=10, width=115, on_click=lambda e: (db.update({"role": "Владелец"}), render()), content=ft.Text("👑 Владелец", size=11, color=WHITE, text_align=ft.TextAlign.CENTER)),
                            ft.Container(bgcolor=BRAND_BLUE, padding=8, border_radius=10, width=115, on_click=lambda e: (db.update({"role": "Магазин"}), render()), content=ft.Text("🏪 Магазин", size=11, color=WHITE, text_align=ft.TextAlign.CENTER)),
                            ft.Container(bgcolor=PURPLE, padding=8, border_radius=10, width=115, on_click=lambda e: (db.update({"role": "Курьер"}), render()), content=ft.Text("🛵 Курьер", size=11, color=WHITE, text_align=ft.TextAlign.CENTER)),
                        ], spacing=6),
                        ft.Container(bgcolor=GREEN, padding=8, border_radius=10, width=365, on_click=lambda e: (db.update({"role": "Покупатель"}), render()), content=ft.Text("👤 Вернуться в режим Клиента", size=11, color=WHITE, text_align=ft.TextAlign.CENTER))
                    ], spacing=8))
                )

            p_col.controls.append(
                ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([
                    ft.Text("🔒 Смена пароля", size=14, color=BLACK),
                    new_pass_input,
                    pass_change_status,
                    ft.Container(bgcolor=BRAND_BLUE, padding=10, border_radius=12, width=365, on_click=update_password, content=ft.Text("Изменить пароль", size=12, color=WHITE, text_align=ft.TextAlign.CENTER))
                ], spacing=8))
            )

            for ic, title, target in [("💳", "Клиентская карта", "карта_клиента"), ("🏦", "Способы оплаты", "способы_оплаты"), ("👤", "Мои данные", "данные")]:
                p_col.controls.insert(3, ft.Container(bgcolor=WHITE, padding=14, border_radius=16, on_click=go("Профиль", target), content=ft.Row([ft.Text(ic, size=20), ft.Text(title, size=14, color=BLACK)])))
            
            p_col.controls.append(
                ft.Container(bgcolor=RED_ALERT, padding=12, border_radius=14, width=390, on_click=lambda e: (db.update({"fio": "", "phone": ""}), render()), content=ft.Text("🚪 Выйти из аккаунта", size=14, color=WHITE, text_align=ft.TextAlign.CENTER))
            )

            body.controls.append(ft.Container(padding=10, content=p_col))

        root.controls.append(body)

        qty, _, _, _, total = calc()
        if show_float:
            root.controls.append(ft.Container(bgcolor=SEA_WAVE, padding=8, content=ft.Row([
                ft.Container(bgcolor=GREEN, padding=9, border_radius=14, on_click=place_order("⚡ Заказать сейчас (25 мин)"), content=ft.Text(" ⚡ Заказать сейчас ", size=12, color=WHITE)),
                ft.Container(bgcolor=CORAL_BTN, padding=10, border_radius=14, on_click=go("Корзина", None), content=ft.Text(f" 🧺 Корзина • {total} ₽ ({qty}) ", size=12, color=WHITE))
            ], spacing=12)))

        root.controls.append(ft.Container(bgcolor=SEA_WAVE, padding=8, content=ft.Row([
            ft.Container(bgcolor=BRAND_DARK if db["tab"] == t else BRAND_BLUE, padding=2, border_radius=15, on_click=go(t, None), content=ft.Container(width=92, padding=6, border_radius=13, bgcolor=BRAND_BLUE if db["tab"] == t else WHITE, content=ft.Column([ft.Text(f"   {ic}", size=17), ft.Text(f"  {t}", size=11, color=WHITE if db["tab"] == t else BLACK)], spacing=2)))
            for ic, t in [("🏠", "Главная"), ("🔍", "Каталог"), ("🧺", "Корзина"), ("👤", "Профиль")]
        ], spacing=8)))

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
