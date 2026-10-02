import flet as ft
from data import *

reject_input = white_field(label_txt="Причина отклонения для покупателя (обязательно)")
chat_msg_input = white_field(hint="Написать сообщение в чат заказа...", w=270)

new_store_name = white_field(label_txt="Название нового магазина", hint="Морской Маркет №3 (Юг)")
new_store_addr = white_field(label_txt="Адрес магазина", hint="г. Краснодар, ул. Ставропольская, 100")
new_user_name = white_field(hint="Имя Фамилия", w=195)
new_user_phone = white_field(hint="Телефон", w=175)

tg_channel_input = white_field(label_txt="Канал/группа Telegram", val=db["tg_channel"], w=250)
post_text_input = white_field(label_txt="Текст нового поста")
post_photo_input = white_field(label_txt="Фото (logo.jpg или URL)", val="logo.jpg")
post_video_input = white_field(label_txt="Видео", val="Видео-обзор поставки (00:40)")

owner_cat_search_input = white_field(hint="🔍 Поиск товара по каталогу...")
new_cat_input = white_field(hint="Название новой категории...", w=255)

ed_name = white_field(label_txt="Название товара")
ed_cat = white_field(label_txt="Категория товара")
ed_base_price = white_field(label_txt="Обычная цена, ₽", w=190)
ed_weight = white_field(label_txt="Вес (напр. 500 г)", w=190)
ed_icon = white_field(label_txt="Иконка (🦐, 🐟, 🥤)", w=390)
ed_is_promo = ft.Switch(value=False)
ed_promo_price = white_field(label_txt="🔥 Новая цена по АКЦИИ, ₽", w=190)
ed_promo_until = white_field(label_txt="⏳ Срок акции (до 20 октября)", w=190)

def render_receipt(order):
    lines = [ft.Text(f"🧾 КАССОВЫЙ ЧЕК ЗАКАЗА №{order['id']}", size=15, color=BLACK)]
    lines.append(ft.Text(f"🏪 Точка сборки: {order['store']}", size=12, color=BRAND_BLUE))
    lines.append(ft.Text(f"🛵 Назначенный курьер: {order['courier']}", size=12, color=PURPLE))
    idx = 1
    for name, q in order["items"].items():
        pinfo = PRODUCTS.get(name, {"price": 300, "weight": "1 шт"})
        row_sum = pinfo["price"] * q
        lines.append(ft.Container(bgcolor=SEA_BG, padding=8, border_radius=10, content=ft.Column([
            ft.Text(f"{idx}. {name} ({pinfo['weight']})", size=13, color=BLACK),
            ft.Row([ft.Text(f"   {q} шт. × {pinfo['price']}.00 ₽", size=12, color=MUTED), ft.Text(f"= {row_sum}.00 ₽", size=13, color=BLACK)], spacing=110)
        ], spacing=2)))
        idx += 1
    lines.append(ft.Container(bgcolor=SEA_WAVE, padding=10, border_radius=12, content=ft.Row([
        ft.Text("ИТОГО ПО ЧЕКУ:", size=15, color=BLACK), ft.Text(f"{order['total']}.00 ₽", size=16, color=BLACK)
    ], spacing=125)))
    return ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column(lines, spacing=6))

def render_chat_window(order, sender, back_fn, render_fn):
    def send_click(e):
        txt = chat_msg_input.value.strip()
        if txt != "":
            order["chat"].append(f"{sender}: {txt}")
            chat_msg_input.value = ""
            render_fn()
    msgs = [ft.Container(bgcolor=WHITE if not m.startswith(sender) else "#E0F2FE", padding=10, border_radius=12, content=ft.Text(m, size=13, color=BLACK)) for m in order["chat"]]
    return ft.Container(padding=10, content=ft.Column([
        ft.Container(bgcolor=WHITE, padding=12, border_radius=14, on_click=back_fn, content=ft.Text(f"← Назад к заказу №{order['id']}", size=14, color=BLACK)),
        sea_divider(f"Чат заказа №{order['id']} ({order['fio']})"),
        ft.Container(bgcolor=SEA_WAVE, padding=10, border_radius=16, content=ft.Column(msgs, spacing=6)),
        ft.Container(bgcolor=WHITE, padding=10, border_radius=16, content=ft.Row([
            chat_msg_input, ft.Container(bgcolor=BRAND_BLUE, padding=12, border_radius=12, on_click=send_click, content=ft.Text("Отпр.", color=WHITE))
        ], spacing=8))
    ], spacing=8))

# =============================================================================
# КАБИНЕТ ВЛАДЕЛЬЦА (ПЕРЕДАЧА РОЛИ ВЛАДЕЛЕЦ, SQLITE ДЛЯ ЛЮДЕЙ И МАГАЗИНОВ)
# =============================================================================
def build_owner_view(body, root, render_fn):
    users_list = load_users_from_db()
    stores_list = load_stores_from_db()

    owner_cat_search_input.on_change = lambda e: (db.update({"owner_search": owner_cat_search_input.value.strip().lower()}), render_fn())

    def delete_user_account(uid):
        def h(e):
            delete_user_from_db(uid)
            render_fn()
        return h

    def delete_store_branch(sid):
        def h(e):
            delete_store_from_db(sid)
            store_names = [s["name"] for s in load_stores_from_db()]
            if db["active_store_name"] not in store_names:
                db["active_store_name"] = store_names[0] if store_names else "Магазины не созданы"
            render_fn()
        return h

    def open_product_editor(target_name):
        def h(e):
            db["owner_edit_target"] = target_name
            if target_name == "__NEW__":
                ed_name.value = ""
                ed_cat.value = db["categories"][0] if db["categories"] else "Разное"
                ed_base_price.value = "500"
                ed_weight.value = "500 г"
                ed_icon.value = "🦐"
                ed_is_promo.value = False
                ed_promo_price.value = "399"
                ed_promo_until.value = "до 20 октября"
            else:
                p = PRODUCTS[target_name]
                ed_name.value = target_name
                ed_cat.value = p["cat"]
                ed_base_price.value = str(p["old_price"] if p["is_promo"] else p["price"])
                ed_weight.value = p["weight"]
                ed_icon.value = p["icon"]
                ed_is_promo.value = p["is_promo"]
                ed_promo_price.value = str(p["price"])
                ed_promo_until.value = p["promo_until"] or "до 20 октября"
            render_fn()
        return h

    def save_product_changes(e):
        old_key = db["owner_edit_target"]
        new_key = ed_name.value.strip() or "Новый товар"
        cat_val = ed_cat.value.strip() or "Разное"
        if cat_val not in db["categories"]:
            db["categories"].append(cat_val)

        try: base_p = int(ed_base_price.value.strip())
        except: base_p = 500
        try: promo_p = int(ed_promo_price.value.strip())
        except: promo_p = base_p

        is_pr = bool(ed_is_promo.value)
        PRODUCTS[new_key] = {
            "price": promo_p if is_pr else base_p,
            "old_price": base_p,
            "weight": ed_weight.value.strip() or "1 шт",
            "icon": ed_icon.value.strip() or "📦",
            "cat": cat_val,
            "is_promo": is_pr,
            "promo_until": ed_promo_until.value.strip() if is_pr else ""
        }
        if old_key != "__NEW__" and old_key in PRODUCTS and old_key != new_key:
            del PRODUCTS[old_key]
        db["owner_edit_target"] = None
        render_fn()

    if db["owner_edit_target"] is not None:
        is_new = (db["owner_edit_target"] == "__NEW__")
        body.controls.append(ft.Container(padding=10, content=ft.Column([
            ft.Container(bgcolor=WHITE, padding=12, border_radius=14, on_click=lambda e: (db.update({"owner_edit_target": None}), render_fn()), content=ft.Text("← Назад в Каталог", size=14, color=BLACK)),
            ft.Container(bgcolor=WHITE, padding=14, border_radius=18, content=ft.Column([
                ft.Text("➕ Новый товар" if is_new else f"✏️ Редактирование: {db['owner_edit_target']}", size=17, color=BRAND_DARK),
                ed_name, ed_cat, ft.Row([ed_base_price, ed_weight], spacing=10), ed_icon,
                ft.Container(bgcolor="#FFF1F2", padding=12, border_radius=14, content=ft.Column([
                    ft.Row([ft.Text("🔥 Включить АКЦИЮ:", size=14, color=RED_ALERT), ed_is_promo], spacing=35),
                    ft.Row([ed_promo_price, ed_promo_until], spacing=10)
                ], spacing=8)),
                ft.Container(bgcolor=GREEN, padding=14, border_radius=14, width=390, on_click=save_product_changes, content=ft.Text("         💾 Сохранить товар", size=14, color=WHITE))
            ], spacing=10))
        ], spacing=10)))
        return

    if db["owner_order_id"] is not None:
        o = get_order_by_id(db["owner_order_id"])
        if o:
            body.controls.append(ft.Container(padding=10, content=ft.Column([
                ft.Container(bgcolor=WHITE, padding=12, border_radius=14, on_click=lambda e: (db.update({"owner_order_id": None}), render_fn()), content=ft.Row([ft.Text("← Назад", size=14, color=BLACK), status_badge(o["state"])], spacing=45)),
                render_receipt(o)
            ], spacing=10)))
            return

    otab = db["owner_tab"]
    col = ft.Column(spacing=10)
    couriers_list = [u for u in users_list if u["role"] == "Курьер"]
    net_revenue = sum(o["total"] for o in db["orders_list"] if o["state"] in ["передан_курьеру", "в_доставке", "доставлен"])

    col.controls.append(ft.Container(bgcolor=BRAND_DARK, padding=12, border_radius=18, content=ft.Row([
        logo(34),
        ft.Column([
            ft.Text("👑 ПАНЕЛЬ ВЛАДЕЛЬЦА И УПРАВЛЯЮЩЕГО", size=13, color=WHITE),
            ft.Text(f"Магазинов: {len(stores_list)} | Курьеров: {len(couriers_list)}", size=11, color=SEA_WAVE)
        ], spacing=2)
    ])))

    # --- ВКЛАДКА 1: 🛍 КАТАЛОГ ---
    if otab == "Каталог":
        col.controls.append(sea_divider(f"🛍 УПРАВЛЕНИЕ КАТАЛОГОМ И АКЦИЯМИ"))
        filter_tabs = ["Все", "🔥 Акции"] + db["categories"]
        cur_cf = db["owner_cat_filter"]

        col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
            owner_cat_search_input,
            ft.Row([
                ft.Container(
                    bgcolor=RED_ALERT if (f == "🔥 Акции" and cur_cf == f) else (BRAND_BLUE if cur_cf == f else SEA_BG),
                    padding=7, border_radius=10, on_click=lambda e, f=f: (db.update({"owner_cat_filter": f}), render_fn()),
                    content=ft.Text(f[:14], size=11, color=WHITE if cur_cf == f else BLACK)
                ) for f in filter_tabs[:4]
            ], spacing=5),
            ft.Container(bgcolor=GREEN, padding=10, border_radius=12, width=390, on_click=open_product_editor("__NEW__"), content=ft.Text("          ➕ Добавить товар в каталог", size=13, color=WHITE))
        ], spacing=8)))

        q_str = db["owner_search"]
        for pname, p in PRODUCTS.items():
            if q_str and q_str not in pname.lower(): continue
            if cur_cf == "🔥 Акции" and not p["is_promo"]: continue
            if cur_cf not in ["Все", "🔥 Акции"] and p["cat"] != cur_cf: continue

            col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Row([
                ft.Container(bgcolor=RED_ALERT if p["is_promo"] else SEA_BG, padding=8, border_radius=12, content=ft.Text("🔥" if p["is_promo"] else p["icon"], size=20)),
                ft.Column([
                    ft.Text(f"{pname} ({p['weight']})", size=14, color=BLACK),
                    ft.Text(f"Цена: {p['price']}.00 ₽" + (f" (Акция до {p['promo_until']})" if p['is_promo'] else ""), size=12, color=RED_ALERT if p['is_promo'] else MUTED)
                ], width=210),
                ft.Container(bgcolor=BRAND_BLUE, padding=8, border_radius=10, width=115, on_click=open_product_editor(pname), content=ft.Text("✏️ Изменить /\n🔥 Акция", size=10, color=WHITE))
            ], spacing=8)))

    # --- ВКЛАДКА 2: 📰 НОВОСТИ И TELEGRAM ---
    elif otab == "Новости":
        col.controls.append(sea_divider("📲 ИНТЕГРАЦИЯ С TELEGRAM"))
        col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, content=ft.Column([
            ft.Row([tg_channel_input, ft.Container(bgcolor=BRAND_BLUE, padding=12, border_radius=12, on_click=lambda e: (db.update({"tg_channel": tg_channel_input.value.strip() or "morskoy_market_official"}), sync_telegram_channel(), render_fn()), content=ft.Text("🔄 Импорт", color=WHITE, size=12))], spacing=8),
            post_text_input, post_photo_input, post_video_input,
            ft.Container(bgcolor=GREEN, padding=12, border_radius=14, width=390, on_click=lambda e: (db["news_posts"].insert(0, {"id": 99, "author": "👑 Владелец", "date": "Только что", "text": post_text_input.value, "photo": post_photo_input.value, "video": post_video_input.value, "is_tg": False}), render_fn()), content=ft.Text("       📢 Опубликовать пост", size=13, color=WHITE))
        ], spacing=8)))
        for p in db["news_posts"]:
            col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
                ft.Row([ft.Text(p["author"], size=12, color=BRAND_BLUE), ft.Container(bgcolor="#FEE2E2", padding=5, border_radius=8, on_click=lambda e, pid=p["id"]: (db.update({"news_posts": [x for x in db["news_posts"] if x["id"] != pid]}), render_fn()), content=ft.Text("🗑 Удалить", size=11, color=RED_ALERT))], spacing=45),
                ft.Text(p["text"], size=13, color=BLACK)
            ], spacing=4)))

    # --- ВКЛАДКА 3: 👥 ЛЮДИ (НАЗНАЧЕНИЕ РОЛИ ВЛАДЕЛЕЦ ДЛЯ ДЕМОНСТРАЦИИ И УДАЛЕНИЕ АККАУНТОВ) ---
    elif otab == "Люди":
        col.controls.append(sea_divider(f"👥 ПОЛЬЗОВАТЕЛИ ({len(users_list)}) • НАЗНАЧЕНИЕ РОЛИ ВЛАДЕЛЕЦ"))

        def set_user_role(uid, new_r):
            def h(e):
                update_user_role_in_db(uid, new_r)
                render_fn()
            return h

        def add_user_click(e):
            nm = new_user_name.value.strip()
            ph = new_user_phone.value.strip() or "+7 (900) 000-00-00"
            if nm != "":
                save_user_to_db(nm, ph, "Покупатель")
                new_user_name.value, new_user_phone.value = "", ""
                render_fn()

        col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
            ft.Row([new_user_name, new_user_phone]),
            ft.Container(bgcolor=BRAND_BLUE, padding=10, border_radius=12, width=390, on_click=add_user_click, content=ft.Text("         ➕ Зарегистрировать пользователя", size=13, color=WHITE))
        ], spacing=8)))

        if users_list:
            col.controls.append(ft.Container(bgcolor=RED_ALERT, padding=10, border_radius=14, width=410, on_click=lambda e: (clear_users_in_db(), render_fn()), content=ft.Text(f"       🚨 Удалить ВСЕХ пользователей ({len(users_list)} чел.)", size=13, color=WHITE)))

        for u in users_list:
            r_col = CORAL_BTN if u["role"] == "Владелец" else (PURPLE if u["role"] == "Курьер" else (BRAND_BLUE if u["role"] == "Магазин" else MUTED))
            col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
                ft.Row([
                    ft.Column([ft.Text(f"👤 {u['name']}", size=14, color=BLACK), ft.Text(u["phone"], size=11, color=MUTED)], width=165),
                    ft.Container(bgcolor=r_col, padding=5, border_radius=8, content=ft.Text(u["role"], size=11, color=WHITE)),
                    ft.Container(bgcolor="#FEE2E2", padding=6, border_radius=8, on_click=delete_user_account(u["id"]), content=ft.Text("🗑", size=11, color=RED_ALERT))
                ], spacing=6),
                ft.Text("Назначить роль (включая Владельца для демонстрации):", size=10, color=MUTED),
                ft.Row([
                    ft.Container(bgcolor=CORAL_BTN if u["role"] == "Владелец" else SEA_BG, padding=6, border_radius=8, width=95, on_click=set_user_role(u["id"], "Владелец"), content=ft.Text("👑 Владелец", size=10, color=WHITE if u["role"] == "Владелец" else BLACK)),
                    ft.Container(bgcolor=PURPLE if u["role"] == "Курьер" else SEA_BG, padding=6, border_radius=8, width=85, on_click=set_user_role(u["id"], "Курьер"), content=ft.Text("🛵 Курьер", size=10, color=WHITE if u["role"] == "Курьер" else BLACK)),
                    ft.Container(bgcolor=BRAND_BLUE if u["role"] == "Магазин" else SEA_BG, padding=6, border_radius=8, width=90, on_click=set_user_role(u["id"], "Магазин"), content=ft.Text("🏪 Магазин", size=10, color=WHITE if u["role"] == "Магазин" else BLACK)),
                    ft.Container(bgcolor=GREEN if u["role"] == "Покупатель" else SEA_BG, padding=6, border_radius=8, width=85, on_click=set_user_role(u["id"], "Покупатель"), content=ft.Text("👤 Клиент", size=10, color=WHITE if u["role"] == "Покупатель" else BLACK)),
                ], spacing=4)
            ], spacing=6)))

    # --- ВКЛАДКА 4: 🏪 МАГАЗИНЫ ---
    elif otab == "Магазины":
        col.controls.append(sea_divider(f"🏪 МАГАЗИНЫ СЕТИ ({len(stores_list)})"))
        def create_store_click(e):
            sn = new_store_name.value.strip()
            sa = new_store_addr.value.strip() or "г. Краснодар"
            if sn != "":
                save_store_to_db(sn, sa)
                new_store_name.value, new_store_addr.value = "", ""
                render_fn()

        col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
            new_store_name, new_store_addr,
            ft.Container(bgcolor=GREEN, padding=10, border_radius=12, width=390, on_click=create_store_click, content=ft.Text("          🏪 Создать магазин", size=13, color=WHITE))
        ], spacing=8)))

        if stores_list:
            col.controls.append(ft.Container(bgcolor=RED_ALERT, padding=10, border_radius=14, width=410, on_click=lambda e: (clear_stores_in_db(), render_fn()), content=ft.Text(f"       🚨 Удалить ВСЕ магазины сети ({len(stores_list)} шт.)", size=13, color=WHITE)))

        for st in stores_list:
            col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Row([
                ft.Column([ft.Text(st["name"], size=14, color=BLACK), ft.Text(st["address"], size=11, color=MUTED)], width=235),
                ft.Container(bgcolor="#FEE2E2", padding=8, border_radius=10, on_click=delete_store_branch(st["id"]), content=ft.Text("🗑 Удалить магазин", size=11, color=RED_ALERT))
            ], spacing=10)))

    # --- ВКЛАДКА 5: 📦 ЗАКАЗЫ ---
    elif otab == "Заказы":
        col.controls.append(sea_divider(f"📦 ВСЕ ЗАКАЗЫ СЕТИ ({len(db['orders_list'])})"))
        if db["orders_list"]:
            col.controls.append(ft.Container(bgcolor=RED_ALERT, padding=10, border_radius=14, width=410, on_click=lambda e: (db["orders_list"].clear(), render_fn()), content=ft.Text(f"       🚨 Удалить ВСЕ заказы из базы ({len(db['orders_list'])} шт.)", size=13, color=WHITE)))
        for o in db["orders_list"]:
            col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=16, content=ft.Column([
                ft.Row([ft.Text(f"Заказ №{o['id']} • {o['total']} ₽", size=15, color=BLACK), status_badge(o["state"])], spacing=45),
                ft.Text(f"🏪 {o['store']} | 🛵 Курьер: {o['courier']}", size=12, color=BRAND_BLUE),
                ft.Row([
                    ft.Container(bgcolor=SEA_BG, padding=7, border_radius=10, width=210, on_click=lambda e, oid=o["id"]: (db.update({"owner_order_id": oid}), render_fn()), content=ft.Text("   🧾 Открыть чек", size=12, color=BLACK)),
                    ft.Container(bgcolor="#FEE2E2", padding=7, border_radius=10, width=165, on_click=lambda e, oid=o["id"]: (db.update({"orders_list": [x for x in db["orders_list"] if x["id"] != oid]}), render_fn()), content=ft.Text("   🗑 Удалить", size=12, color=RED_ALERT))
                ], spacing=10)
            ], spacing=5)))

    body.controls.append(ft.Container(padding=10, content=col))

    root.controls.append(ft.Container(bgcolor=SEA_WAVE, padding=8, content=ft.Row([
        ft.Container(
            bgcolor=BRAND_DARK if db["owner_tab"] == t else BRAND_BLUE, padding=2, border_radius=13,
            on_click=lambda e, t=t: (db.update({"owner_tab": t, "owner_order_id": None, "owner_edit_target": None}), render_fn()),
            content=ft.Container(width=72, padding=5, border_radius=11, bgcolor=BRAND_BLUE if db["owner_tab"] == t else WHITE, content=ft.Column([ft.Text(f"  {ic}", size=15), ft.Text(t, size=10, color=WHITE if db["owner_tab"] == t else BLACK)], spacing=1))
        ) for ic, t in [("🛍", "Каталог"), ("📰", "Новости"), ("👥", "Люди"), ("🏪", "Магазины"), ("📦", "Заказы")]
    ], spacing=5)))

def build_staff_view(role, body, root, render_fn):
    is_store = (role == "Магазин")
    stores_list = load_stores_from_db()
    store_names = [s["name"] for s in stores_list]
    if db["active_store_name"] not in store_names and store_names:
        db["active_store_name"] = store_names[0]

    act_key = "store_active_id" if is_store else "courier_active_id"
    mode_key = "store_mode" if is_store else "courier_mode"
    err_key = "store_reject_err" if is_store else "courier_reject_err"

    def open_ord(oid, m="detail"):
        def h(e):
            db[act_key], db[mode_key], db[err_key] = oid, m, False
            reject_input.value = ""
            render_fn()
        return h

    def set_st(oid, new_st, msg):
        def h(e):
            o = get_order_by_id(oid)
            if o:
                o["state"] = new_st
                if not is_store and new_st == "в_доставке":
                    o["courier"] = db["active_courier_name"]
                o["chat"].append(msg)
            render_fn()
        return h

    def do_reject(oid):
        def h(e):
            reason = reject_input.value.strip()
            if reason == "":
                db[err_key] = True
                render_fn()
                return
            o = get_order_by_id(oid)
            if o:
                if is_store: o["state"], o["reject_reason"] = "отклонен", reason
                else: o["state"], o["courier"] = "поиск_курьера", "Не назначен"
                db[act_key] = None
            render_fn()
        return h

    if db[act_key] is not None:
        ord_obj = get_order_by_id(db[act_key])
        if ord_obj is None:
            db[act_key] = None
            render_fn()
            return
        if db[mode_key] == "chat":
            body.controls.append(render_chat_window(ord_obj, role, open_ord(ord_obj["id"], "detail"), render_fn))
            return
        if db[mode_key] == "reject":
            body.controls.append(ft.Container(padding=10, content=ft.Column([
                ft.Container(bgcolor=WHITE, padding=12, border_radius=14, on_click=open_ord(ord_obj["id"], "detail"), content=ft.Text("← Назад", size=14, color=BLACK)),
                ft.Container(bgcolor=WHITE, padding=16, border_radius=16, content=ft.Column([
                    ft.Text(f"❌ Отклонение заказа №{ord_obj['id']}", size=18, color=RED_ALERT),
                    reject_input,
                    ft.Container(bgcolor=RED_ALERT, padding=14, border_radius=14, width=390, on_click=do_reject(ord_obj["id"]), content=ft.Text("Подтвердить отказ", color=WHITE, size=14))
                ], spacing=10))
            ], spacing=10)))
            return

        det = ft.Column(spacing=10)
        det.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=14, on_click=open_ord(None), content=ft.Row([ft.Text("← Назад", size=14, color=BLACK), status_badge(ord_obj["state"])], spacing=55)))
        need_accept = (is_store and ord_obj["state"] == "новый") or (not is_store and ord_obj["state"] in ["поиск_курьера", "передан_курьеру"])
        if need_accept:
            next_st = "принят" if is_store else "в_доставке"
            det.controls.append(ft.Container(bgcolor=WHITE, padding=16, border_radius=16, content=ft.Column([
                ft.Text(f"🔔 Заказ №{ord_obj['id']} ({ord_obj['total']}.00 ₽)", size=17, color=BLACK),
                ft.Row([
                    ft.Container(bgcolor=GREEN, padding=14, border_radius=14, width=190, on_click=set_st(ord_obj["id"], next_st, "Принят"), content=ft.Text("✅ Принять", color=WHITE, size=14)),
                    ft.Container(bgcolor=RED_ALERT, padding=14, border_radius=14, width=180, on_click=open_ord(ord_obj["id"], "reject"), content=ft.Text("❌ Отклонить", color=WHITE, size=14))
                ], spacing=12)
            ], spacing=10)))
        else:
            det.controls.append(render_receipt(ord_obj))
        body.controls.append(ft.Container(padding=10, content=det))
        return

    if is_store:
        store_orders = [o for o in db["orders_list"] if o["store"] == db["active_store_name"]]
        col = ft.Column([sea_divider(f"ОЧЕРЕДЬ: {db['active_store_name']}")], spacing=10)
        for o in store_orders:
            col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, on_click=open_ord(o["id"], "detail"), content=ft.Row([
                ft.Text(f"Заказ №{o['id']} • {o['total']} ₽ ({o['fio']})", size=14, color=BLACK), status_badge(o["state"])
            ], spacing=25)))
        body.controls.append(ft.Container(padding=10, content=col))
    else:
        col = ft.Column([sea_divider(f"ДОСТАВКИ КУРЬЕРА ({db['active_courier_name']})")], spacing=10)
        for o in db["orders_list"]:
            col.controls.append(ft.Container(bgcolor=WHITE, padding=14, border_radius=16, on_click=open_ord(o["id"], "detail"), content=ft.Row([
                ft.Text(f"Заказ №{o['id']} • {o['address']}", size=13, color=BLACK), status_badge(o["state"])
            ], spacing=25)))
        body.controls.append(ft.Container(padding=10, content=col))