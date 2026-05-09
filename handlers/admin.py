from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import re

from config import ADMIN_ID
from utils import get_user_by_code, update_balance

router = Router()

# ==================
# STATE (per admin) - ISOLATED FROM REGULAR USERS
# ==================
admin_mode = {}  # Track what admin is doing: "topup", "price", None
awaiting_user = {}
pending_user = {}
pending_amount = {}

awaiting_service_id = {}
pending_service_id = {}
awaiting_price = {}
pending_price = {}

# ==================
# ADMIN MENU
# ==================
admin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💰 Hisobni to'ldirish", callback_data="admin_topup")],
        [InlineKeyboardButton(text="📦 Buyurtmalarni ko'rish", callback_data="admin_orders")],
        [InlineKeyboardButton(text="💸 Narxni o'zgartirish", callback_data="admin_price")]
    ]
)


# ==================
# ADMIN PANEL
# ==================
@router.message(F.text == "👨‍💼 Admin panel")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz")
        return
    await message.answer("⚙️ Admin panel:", reply_markup=admin_kb)


# ==================
# TOPUP START
# ==================
@router.callback_query(F.data == "admin_topup")
async def admin_topup(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_mode[call.from_user.id] = "topup"
    awaiting_user[call.from_user.id] = True
    await call.message.answer("👤 Foydalanuvchi ID kiriting (00001):")
    await call.answer()


# ==================
# USER ID OLISH
# ==================
@router.message(lambda m: m.text and m.from_user.id == ADMIN_ID and awaiting_user.get(m.from_user.id))
async def get_user_id(message: Message):
    admin_id = message.from_user.id
    if not awaiting_user.get(admin_id):
        return
    
    # Safety check: ensure admin is in topup mode
    if admin_mode.get(admin_id) != "topup":
        return

    if not re.match(r'^\d{5}$', message.text):
        await message.answer("❌ 5 xonali ID kiriting (masalan: 00001)")
        return

    user = get_user_by_code(message.text)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi")
        return

    tg_id = user[1]
    user_code = user[2]
    balance = user[3]

    pending_user[admin_id] = {"user_code": user_code, "tg_id": tg_id}
    awaiting_user[admin_id] = False

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1000", callback_data="amt_1000"),
                InlineKeyboardButton(text="2000", callback_data="amt_2000")
            ],
            [
                InlineKeyboardButton(text="5000", callback_data="amt_5000"),
                InlineKeyboardButton(text="10000", callback_data="amt_10000")
            ]
        ]
    )

    await message.answer(f"👤 USER:\n🆔 {user_code}\n💰 {balance} so'm")
    await message.answer("💰 Summani tanlang:", reply_markup=kb)


# ==================
# AMOUNT SELECT
# ==================
@router.callback_query(F.data.startswith("amt_"))
async def select_amount(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    amount = int(call.data.split("_")[1])
    pending_amount[call.from_user.id] = amount
    data = pending_user.get(call.from_user.id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # FIX: "topup_confirm" va "topup_cancel" - "confirm"/"cancel" emas
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="topup_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="topup_cancel")
            ]
        ]
    )
    await call.message.answer(
        f"⚠️ ID: {data['user_code']}\n💰 {amount} so'm",
        reply_markup=kb
    )
    await call.answer()


# ==================
# TOPUP CONFIRM/CANCEL
# FIX: "confirm" → "topup_confirm", "cancel" → "topup_cancel"
# ==================
@router.callback_query(F.data == "topup_confirm")
async def confirm(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_id = call.from_user.id
    data = pending_user.get(admin_id)
    amount = pending_amount.get(admin_id)

    if not data:
        await call.answer("❌ Ma'lumot topilmadi")
        return

    update_balance(data["user_code"], amount)

    # Clear admin state
    admin_mode.pop(admin_id, None)
    awaiting_user.pop(admin_id, None)
    pending_user.pop(admin_id, None)
    pending_amount.pop(admin_id, None)

    await call.message.answer(f"✅ {data['user_code']} hisobiga {amount} so'm qo'shildi")
    await call.bot.send_message(
        data["tg_id"],
        f"💰 Hisobingiz {amount} so'm ga to'ldirildi"
    )

    await call.answer()


@router.callback_query(F.data == "topup_cancel")
async def cancel(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_id = call.from_user.id
    
    # Clear admin state
    admin_mode.pop(admin_id, None)
    awaiting_user.pop(admin_id, None)
    pending_user.pop(admin_id, None)
    pending_amount.pop(admin_id, None)
    
    await call.message.answer("❌ Bekor qilindi")
    await call.answer()


# ==================
# NARX O'ZGARTIRISH
# ==================
@router.callback_query(F.data == "admin_price")
async def admin_price(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    admin_id = call.from_user.id
    admin_mode[admin_id] = "price"
    awaiting_service_id[admin_id] = True

    from handlers.smm import SERVICES
    services_text = "📋 Mavjud xizmatlar:\n\n"
    for key, service in SERVICES.items():
        services_text += f"🆔 {service['id']} - {service['name']} ({service['price']} so'm)\n"
    services_text += "\n🔧 Xizmat ID raqamini kiriting:"

    await call.message.answer(services_text)
    await call.answer()


@router.message(lambda m: m.text and m.from_user.id == ADMIN_ID and awaiting_service_id.get(m.from_user.id))
async def get_service_id(message: Message):
    admin_id = message.from_user.id
    if not awaiting_service_id.get(admin_id):
        return

    # Safety check: ensure admin is in price mode
    if admin_mode.get(admin_id) != "price":
        return

    if not re.match(r'^\d{2}$', message.text):
        await message.answer("❌ 2 xonali ID kiriting (masalan: 01)")
        return

    service_id = message.text
    from handlers.smm import SERVICES
    service_key = next((k for k, v in SERVICES.items() if v["id"] == service_id), None)

    if not service_key:
        await message.answer("❌ Bunday xizmat ID mavjud emas")
        return

    pending_service_id[admin_id] = {
        "service_id": service_id,
        "service_key": service_key,
        "service_name": SERVICES[service_key]["name"],
        "current_price": SERVICES[service_key]["price"]
    }
    awaiting_service_id[admin_id] = False
    awaiting_price[admin_id] = True

    await message.answer(
        f"🔧 Xizmat: {SERVICES[service_key]['name']}\n"
        f"💰 Joriy narx: {SERVICES[service_key]['price']} so'm\n\n"
        f"💵 Yangi narxni kiriting:"
    )


@router.message(lambda m: m.text and m.from_user.id == ADMIN_ID and awaiting_price.get(m.from_user.id))
async def get_price(message: Message):
    admin_id = message.from_user.id
    if not awaiting_price.get(admin_id):
        return

    # Safety check: ensure admin is in price mode
    if admin_mode.get(admin_id) != "price":
        return

    if not re.match(r'^\d+$', message.text):
        await message.answer("❌ Faqat raqam kiriting")
        return

    price = int(message.text)
    service_data = pending_service_id.get(admin_id)
    if not service_data:
        return

    pending_price[admin_id] = price
    awaiting_price[admin_id] = False

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="price_confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="price_cancel")
            ]
        ]
    )
    await message.answer(
        f"⚠️ NARX O'ZGARTIRISH\n\n"
        f"🔧 {service_data['service_name']}\n"
        f"🆔 ID: {service_data['service_id']}\n"
        f"💰 Joriy: {service_data['current_price']} so'm\n"
        f"💵 Yangi: {price} so'm",
        reply_markup=kb
    )


# FIX: "confirm_price" → "price_confirm", "cancel_price" → "price_cancel"
@router.callback_query(F.data == "price_confirm")
async def confirm_price_change(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    admin_id = call.from_user.id
    service_data = pending_service_id.get(admin_id)
    new_price = pending_price.get(admin_id)

    if not service_data or new_price is None:
        await call.message.answer("❌ Xatolik yuz berdi")
        return

    # Memory'da yangilash
    from handlers.smm import SERVICES
    SERVICES[service_data["service_key"]]["price"] = new_price

    # DB da ham saqlash (restart'dan keyin ham saqlansin)
    from utils import save_service_price
    save_service_price(service_data["service_key"], new_price)

    # Clear ALL admin state for this user
    admin_mode.pop(admin_id, None)
    awaiting_service_id.pop(admin_id, None)
    pending_service_id.pop(admin_id, None)
    awaiting_price.pop(admin_id, None)
    pending_price.pop(admin_id, None)

    await call.message.answer(
        f"✅ Narx o'zgartirildi!\n\n"
        f"🔧 {service_data['service_name']}\n"
        f"💵 {new_price} so'm"
    )
    await call.answer()


@router.callback_query(F.data == "price_cancel")
async def cancel_price_change(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    admin_id = call.from_user.id
    # Clear ALL admin state for this user
    admin_mode.pop(admin_id, None)
    awaiting_service_id.pop(admin_id, None)
    pending_service_id.pop(admin_id, None)
    awaiting_price.pop(admin_id, None)
    pending_price.pop(admin_id, None)

    await call.message.answer("❌ Narx o'zgartirish bekor qilindi")
    await call.answer()


# ==================
# BUYURTMALAR
# ==================
@router.callback_query(F.data == "admin_orders")
async def admin_orders(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status='pending' ORDER BY id DESC LIMIT 5")
    orders = cursor.fetchall()
    conn.close()

    if not orders:
        await call.message.answer("📦 Kutilayotgan buyurtmalar yo'q")
        await call.answer()
        return

    text = "📦 KUTILAYOTGAN BUYURTMALAR:\n\n"
    kb_rows = []

    for order in orders:
        text += (
            f"🆔 {order[0]} | 👤 {order[1]} | 🔧 {order[2]} | "
            f"🔢 {order[3]} | 💰 {order[5]} so'm\n"
        )
        # FIX: "order_approve_" va "order_cancel_" prefixi
        kb_rows.append([
            InlineKeyboardButton(text=f"✅ #{order[0]}", callback_data=f"order_approve_{order[0]}"),
            InlineKeyboardButton(text=f"❌ #{order[0]}", callback_data=f"order_cancel_{order[0]}")
        ])

    kb_rows.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_orders")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)

    await call.answer()


# FIX: "approve_" → "order_approve_"
@router.callback_query(F.data.startswith("order_approve_"))
async def approve_order(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    order_id = int(call.data.split("_")[2])

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()

    if not order:
        await call.message.answer("❌ Buyurtma topilmadi")
        conn.close()
        await call.answer()
        return

    if order[6] != "pending":
        await call.message.answer("❌ Bu buyurtma allaqachon ko'rib chiqilgan")
        conn.close()
        await call.answer()
        return

    cursor.execute("UPDATE orders SET status='completed' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

    try:
        await call.bot.send_message(
            order[1],
            f"✅ Buyurtmangiz (#{order_id}) bajarildi!\n\n"
            f"🔧 Xizmat: {order[2]}\n"
            f"🔢 Miqdor: {order[3]}\n"
            f"💰 Summa: {order[5]} so'm"
        )
    except Exception as e:
        print(f"User notification failed: {e}")

    await call.message.answer(f"✅ Buyurtma #{order_id} bajarildi")
    await call.answer()


# FIX: "cancel_" → "order_cancel_"
@router.callback_query(F.data.startswith("order_cancel_"))
async def cancel_order(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    order_id = int(call.data.split("_")[2])

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()

    if not order:
        await call.message.answer("❌ Buyurtma topilmadi")
        conn.close()
        await call.answer()
        return

    if order[6] != "pending":
        await call.message.answer("❌ Bu buyurtma allaqachon ko'rib chiqilgan")
        conn.close()
        await call.answer()
        return

    cursor.execute("UPDATE orders SET status='canceled' WHERE id=?", (order_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE tg_id=?", (order[5], order[1]))
    conn.commit()
    conn.close()

    try:
        await call.bot.send_message(
            order[1],
            f"❌ Buyurtmangiz (#{order_id}) bekor qilindi.\n\n"
            f"💰 {order[5]} so'm hisobingizga qaytarildi.\n\n"
            f"🔧 Xizmat: {order[2]}\n"
            f"🔢 Miqdor: {order[3]}"
        )
    except Exception as e:
        print(f"User notification failed: {e}")

    await call.message.answer(f"❌ Buyurtma #{order_id} bekor qilindi")
    await call.answer()
