import os
import flet as ft
from data import *
from staff import build_staff_view, build_owner_view, render_chat_window

def main(page):
    page.title = "Морской Маркет — Доставка"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 445
    page.window.height = 865
    page.bgcolor = SEA_BG
    page.padding = 0

    # Поля для экрана регистрации при первом запуске
    reg_name_input = white_field(label_txt="Ваше Имя и Фамилия", hint="Иван Иванов")
    reg_phone_input = white_field(label_txt="Номер телефона", hint="+7 (900) 000-00-00")
    
    selected_reg_role = {"role": "Покупатель"}

    def set_reg_role(r):
        def h(e):
            selected_reg_role["role"] = r
            render()
        return h

    def register_new_user(e):
        name = reg_name_input.value.strip()
        phone = reg_phone_input.value.strip()
        if name != "" and phone != "":
            save_user_to_db(name, phone, selected_reg_role["role"])
            db["fio"] = name
            db["phone"] = phone
            db["role"] = selected_reg_role["role"]
            render()

    search_input = white_field(hint="🔍 Поиск по витрине...")
    comment_input = white_field(label_txt="Пожелания сборщику", val=db["comment"])

    fio_input = white_field(label_txt="Имя и Фамилия", val=db["fio"])
    phone_input = white_field(label_txt="Телефон", val=db["phone"])
    addr_input = white_field(label_txt="Адрес доставки", val=db["address"])
    intercom_input = white_field(label_txt="Домофон", val=db["intercom"])

    root = ft.Column(spacing=0)
    main_screen = ft.Container(bgcolor=SEA_BG, width=445, height=845, content=root)

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
        
        users_in_db = load_users_from_db()
        if not users_in_db:
            reg_col = ft.Column([
                ft.Container(height=40),
                logo(54),
                ft.Text("🌊 МОРСКОЙ МАРКЕТ", size=22, color=BRAND_DARK),
                ft.Text("Добро пожаловать! Зарегистрируйтесь для начала работы.", size=12, color=MUTED),
                reg_name_input,
                reg_phone_input,
                ft.Text("Выберите вашу стартовую роль:", size=13, color=BLACK),
                ft.Row([
                    ft.Container(bgcolor=CORAL_BTN if selected_reg_role["role"] == "Владелец" else SEA_BG, padding=10, border_radius=12, width=120, on_click=set_reg_role("Владелец"), content=ft.Text("👑 Владелец", size=12, color=WHITE if selected_reg_role["role"] == "Владелец" else BLACK)),
                    ft.Container(bgcolor=BRAND_BLUE if selected_reg_role["role"] == "Покупатель" else SEA_BG, padding=10, border_radius=12, width=125, on_click=set_reg_role("Покупатель"), content=ft.Text("👤 Покупатель", size=12, color=WHITE if selected_reg_role["role"] == "Покупатель" else BLACK)),
                ], spacing=8),
                ft.Container(height=10),
                ft.Container(bgcolor=GREEN, padding=14, border_radius=16, width=390, on_click=register_new_user, content=ft.Text("        🚀 Зарегистрироваться и войти", size=14, color=WHITE))
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            root.controls.append(ft.Container(bgcolor=WHITE, padding=20, border_radius=20, width=425, height=820, content=reg_col))
            page.update()
            return

        qty, s, pack, save, total = calc()
        c_cnt = sum(1 for o in db["orders_list"] if o["state"] in ["поиск_курьера", "передан_курьеру", "в_доставке"])

        root.controls.append(ft.Container(bgcolor=BRAND_DARK, padding=7, content=ft.Row([
            ft.Container(content=ft.Text("👤 Клиент", color=WHITE, size=11), bgcolor=BRAND_BLUE if db["role"] == "Покупатель" else "#1E3A4C", padding=6, border_radius=8, on_click=lambda e: (db.update({"role": "Покупатель"}), render())),
            ft.Container(content=ft.Text("🏪 Магазин", color=WHITE, size=11), bgcolor=BRAND_BLUE if db["role"] == "Магазин" else "#1E3A4C", padding=6, border_radius=8, on_click=lambda e: (db.update({"role": "Магазин"}), render())),
            ft.Container(content=ft.Text("🛵 Курьер", color=WHITE, size=11), bgcolor=BRAND_BLUE if db["role"] == "Курьер" else "#1E3A4C", padding=6, border_radius=8, on_click=lambda e: (db.update({"role": "Курьер"}), render())),
            ft.Container(content=ft.Text("👑 Владелец", color=WHITE, size=11), bgcolor=CORAL_BTN if db["role"] == "Владелец" else "#1E3A4C", padding=6, border_radius=8, on_click=lambda e: (db.update({"role": "Владелец"}), render())),
        ], spacing=5)))

        show_float = (db["role"] == "Покупатель" and db["tab"] in ["Главная", "Каталог"] and db["subscreen"] in [None, "акции"] and db["client_chat_id"] is None and qty > 0)
        body = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=555 if show_float else 640)

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
                news_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=18, content=ft.Column([ft.Text(p["author"], size=13, color=BRAND_BLUE), ft.Text(p["text"], size=13, color=BLACK)], spacing=6)))
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
                sea_divider("Морская витрина • Хиты дня")
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
            c_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([
                comment_input,
                ft.Row([ft.Text("Итого", size=18, color=BLACK), ft.Text(f"{total} ₽", size=18, color=BLACK)], spacing=215),
                ft.Container(bgcolor=GREEN, padding=12, border_radius=14, width=385, on_click=place_order(now_slot), content=ft.Text("  ⚡ Оформить заказ", color=WHITE, size=14))
            ], spacing=8)))
            body.controls.append(ft.Container(padding=10, content=c_col))

        elif db["tab"] == "Профиль":
            p_col = ft.Column([render_client_card(), render_news_and_promo_blocks(), sea_divider("Личный кабинет")], spacing=10)
            for ic, title, target in [("💳", "Клиентская карта", "карта_клиента"), ("🏦", "Способы оплаты", "способы_оплаты"), ("👤", "Мои данные", "данные")]:
                p_col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, on_click=go("Профиль", target), content=ft.Row([ft.Text(ic, size=20), ft.Text(title, size=14, color=BLACK)])))
            body.controls.append(ft.Container(padding=10, content=p_col))

        root.controls.append(body)

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

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
