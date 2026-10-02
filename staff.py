import flet as ft
from data import *

def build_staff_view(role, body_col, root_col, render_callback):
    body_col.controls.clear()
    
    is_store = (role == "Магазин")
    active_orders = [o for o in db["orders_list"] if o["state"] in ["новый", "принят", "поиск_курьера", "передан_курьеру", "в_доставке"]]
    
    header = ft.Container(
        bgcolor=BRAND_DARK, padding=12, border_radius=12,
        content=ft.Row([
            ft.Text(f"🏪 ПАНЕЛЬ МАГАЗИНА" if is_store else f"🛵 ПАНЕЛЬ КУРЬЕРА", size=14, color=WHITE),
            ft.Container(
                bgcolor=CORAL_BTN, padding=6, border_radius=8,
                on_click=lambda e: (db.update({"fio": "", "phone": ""}), render_callback()),
                content=ft.Text("🚪 Выход", size=11, color=WHITE)
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )
    body_col.controls.append(header)
    
    if not active_orders:
        body_col.controls.append(ft.Container(padding=20, content=ft.Text("Нет активных заказов", size=13, color=MUTED, text_align=ft.TextAlign.CENTER)))
    
    for o in active_orders:
        oid = o["id"]
        st = o["state"]
        
        actions = []
        if is_store and st == "новый":
            actions.append(ft.Container(bgcolor=GREEN, padding=8, border_radius=8, on_click=lambda e, id=oid: accept_order(id, render_callback), content=ft.Text("✅ Принять в сборку", size=11, color=WHITE)))
        elif is_store and st == "принят":
            actions.append(ft.Container(bgcolor=BRAND_BLUE, padding=8, border_radius=8, on_click=lambda e, id=oid: call_courier(id, render_callback), content=ft.Text("🔍 Вызвать курьера", size=11, color=WHITE)))
        elif not is_store and st in ["поиск_курьера", "передан_курьеру"]:
            actions.append(ft.Container(bgcolor=PURPLE, padding=8, border_radius=8, on_click=lambda e, id=oid: deliver_order(id, render_callback), content=ft.Text("🛵 Забрать и в путь", size=11, color=WHITE)))
        elif not is_store and st == "в_доставке":
            actions.append(ft.Container(bgcolor=GREEN, padding=8, border_radius=8, on_click=lambda e, id=oid: finish_order(id, render_callback), content=ft.Text("🎉 Доставлено клиенту", size=11, color=WHITE)))

        card_content = ft.Column([
            ft.Row([ft.Text(f"Заказ №{oid}", size=14, color=BLACK), status_badge(st)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"👤 Клиент: {o['fio']} ({o['phone']})", size=12, color=BLACK),
            ft.Text(f"📍 Адрес: {o['address']}", size=12, color=MUTED),
            ft.Text(f"💬 Пожелания: {o['comment']}", size=11, color=BRAND_DARK) if o['comment'] else ft.Container(),
            ft.Row(actions, spacing=6)
        ], spacing=6)

        body_col.controls.append(ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=card_content))

def accept_order(oid, render_cb):
    o = get_order_by_id(oid)
    if o:
        o["state"] = "принят"
        o["chat"].append("Магазин: Заказ принят в сборку.")
    render_cb()

def call_courier(oid, render_cb):
    o = get_order_by_id(oid)
    if o:
        o["state"] = "поиск_курьера"
        o["chat"].append("Магазин: Заказ собран, идет поиск курьера.")
    render_cb()

def deliver_order(oid, render_cb):
    o = get_order_by_id(oid)
    if o:
        o["state"] = "в_доставке"
        o["courier"] = db["fio"]
        o["chat"].append(f"Курьер {db['fio']} забрал заказ и выехал в путь.")
    render_cb()

def finish_order(oid, render_cb):
    o = get_order_by_id(oid)
    if o:
        o["state"] = "доставлен"
        o["chat"].append("Система: Заказ успешно доставлен!")
    render_cb()

def build_owner_view(body_col, root_col, render_callback):
    body_col.controls.clear()
    
    stores_count = len(load_stores_from_db())
    users_count = len(load_users_from_db())
    
    header = ft.Container(
        bgcolor=BRAND_DARK, padding=12, border_radius=16,
        content=ft.Column([
            ft.Row([
                ft.Row([logo(28), ft.Text("ПАНЕЛЬ ВЛАДЕЛЬЦА", size=14, color=WHITE)], spacing=8),
                ft.Container(
                    bgcolor=CORAL_BTN, padding=6, border_radius=8,
                    on_click=lambda e: (db.update({"role": "Покупатель", "tab": "Профиль"}), render_callback()),
                    content=ft.Row([ft.Text("👤", size=14), ft.Text("Профиль", size=11, color=WHITE)], spacing=4)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"Магазинов в сети: {stores_count} | Пользователей: {users_count}", size=11, color=SEA_BG)
        ], spacing=6)
    )
    body_col.controls.append(header)
    
    # Блок настройки Telegram-канала с автоочисткой ссылок
    tg_input = white_field(val=db["tg_channel"], hint="morskie_delikatesy или https://t.me/...")
    
    def save_tg(e):
        cleaned = clean_tg_link(tg_input.value)
        db["tg_channel"] = cleaned
        save_db_setting("tg_channel", cleaned)
        sync_telegram_channel()
        render_callback()

    body_col.controls.append(
        ft.Container(bgcolor=WHITE, padding=12, border_radius=14, content=ft.Column([
            ft.Text("📢 Управление Telegram-каналом новостей", size=13, color=BLACK),
            tg_input,
            ft.Row([
                ft.Container(bgcolor=BRAND_BLUE, padding=8, border_radius=10, on_click=save_tg, content=ft.Text("💾 Сохранить и обновить", size=11, color=WHITE)),
                ft.Container(bgcolor=GREEN, padding=8, border_radius=10, on_click=lambda e: (sync_telegram_channel(), render_callback()), content=ft.Text("🔄 Синхронизировать", size=11, color=WHITE))
            ], spacing=8)
        ], spacing=8))
    )
    
    body_col.controls.append(sea_divider("Управление каталогом и акциями"))
    
    for pname, pdata in PRODUCTS.items():
        p_card = ft.Container(
            bgcolor=WHITE, padding=12, border_radius=14,
            content=ft.Row([
                ft.Row([ft.Text(pdata['icon'], size=24), ft.Column([ft.Text(pname, size=13, color=BLACK), ft.Text(f"Цена: {pdata['price']} ₽ ({pdata['weight']})", size=11, color=MUTED)], spacing=2)], spacing=10),
                ft.Container(
                    bgcolor=BRAND_BLUE, padding=8, border_radius=10,
                    on_click=lambda e, name=pname: toggle_promo(name, render_callback),
                    content=ft.Text("🔥 Акция" if not pdata['is_promo'] else "✓ Активен", size=11, color=WHITE)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
        body_col.controls.append(p_card)

def toggle_promo(pname, render_cb):
    if pname in PRODUCTS:
        PRODUCTS[pname]["is_promo"] = not PRODUCTS[pname]["is_promo"]
    render_cb()

def render_chat_window(order, current_role, back_callback, render_cb):
    if not order:
        return ft.Container()
    
    msg_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, height=350)
    for m in order["chat"]:
        msg_list.controls.append(ft.Container(bgcolor=WHITE, padding=8, border_radius=10, content=ft.Text(m, size=12, color=BLACK)))
        
    chat_input = white_field(hint="Введите сообщение...")
    
    def send_msg(e):
        txt = chat_input.value.strip()
        if txt:
            order["chat"].append(f"{current_role}: {txt}")
            chat_input.value = ""
            render_cb()

    return ft.Column([
        ft.Container(bgcolor=WHITE, padding=10, border_radius=12, content=ft.Row([ft.Container(on_click=back_callback, content=ft.Text("← Назад к заказам", size=13, color=BLACK))])),
        sea_divider(f"💬 Чат по заказу №{order['id']}"),
        msg_list,
        ft.Row([chat_input, ft.Container(bgcolor=GREEN, padding=10, border_radius=10, on_click=send_msg, content=ft.Text("Отправить", size=12, color=WHITE))], spacing=6)
    ], spacing=10)
