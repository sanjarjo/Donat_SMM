from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import sqlite3
from config import ADMIN_ID

router = Router()

user_page = {}

def get_orders(user_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (user_id,))
    return cursor.fetchall()

@router.message(lambda m: m.text and m.text.strip() == "📦 Buyurtmalarim")
async def my_orders(message: Message):

    orders = get_orders(message.from_user.id)

    if not orders:
        await message.answer("❌ Buyurtmalar yo‘q")
        return

    user_page[message.from_user.id] = 0

    await show_order(message, orders, 0)

async def show_order(message, orders, index):

    order = orders[index]

    text = (
        f"📦 BUYURTMA\n\n"
        f"🆔 ID: {order[0]}\n"
        f"🔧 Xizmat: {order[2]}\n"
        f"📅 Sana: {order[7]}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="prev"),
                InlineKeyboardButton(text="➡️", callback_data="next")
            ],
            [
                InlineKeyboardButton(text="📄 Batafsil", callback_data=f"detail_{order[0]}")
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "next")
async def next_order(call: CallbackQuery):

    orders = get_orders(call.from_user.id)
    index = user_page.get(call.from_user.id, 0)

    if index + 1 < len(orders):
        index += 1
        user_page[call.from_user.id] = index
        await show_order(call.message, orders, index)

    await call.answer()


@router.callback_query(F.data == "prev")
async def prev_order(call: CallbackQuery):

    index = user_page.get(call.from_user.id, 0)

    if index > 0:
        index -= 1
        user_page[call.from_user.id] = index

        orders = get_orders(call.from_user.id)
        await show_order(call.message, orders, index)

    await call.answer()

@router.callback_query(F.data.startswith("detail_"))
async def detail(call: CallbackQuery):

    order_id = int(call.data.split("_")[1])

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order = cursor.fetchone()

    text = (
        f"📄 BATAFSIL\n\n"
        f"🆔 {order[0]}\n"
        f"📊 Status: {order[6]}\n"
        f"🔗 Link: {order[4]}\n"
        f"🔢 Miqdor: {order[3]}\n"
        f"💰 Summa: {order[5]}"
    )

    await call.message.answer(text)
    await call.answer()
    
def create_order(user_id, service_id, qty, link, amount):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO orders (user_id, service_id, qty, link, amount, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        service_id,
        qty,
        link,
        amount,
        "pending",
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()
    conn.close()

# =========================
# STATE
# =========================
user_step = {}
user_service = {}
user_qty = {}
user_link = {}
user_game_id = {}
user_game_zone = {}

# =========================
# MAIN MENU
# =========================
smm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📲 Telegram", callback_data="smm_telegram"),
            InlineKeyboardButton(text="📸 Instagram", callback_data="smm_instagram")
        ]
    ]
)

# TELEGRAM MENU
telegram_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👥 Obunachi", callback_data="tg_subs")],
        [InlineKeyboardButton(text="🇺🇿 O'zbek Obunachi", callback_data="uzbek_subs")],
        [InlineKeyboardButton(text="👁️ ko'rishlar", callback_data="tg_views")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_smm")]
    ]
)

# OBUNACHI MENU
subs_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="30 kun", callback_data="sub_30"),
            InlineKeyboardButton(text="60 kun", callback_data="sub_60")
        ],
        [
            InlineKeyboardButton(text="90 kun", callback_data="sub_90"),
            InlineKeyboardButton(text="120 kun", callback_data="sub_120")
        ],
        [
            InlineKeyboardButton(text="180 kun", callback_data="sub_180"),
            InlineKeyboardButton(text="365 kun", callback_data="sub_365")
        ],
        [
            InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_telegram")
        ]
    ]
)

# UZBEK OBUNACHI MENU
uzbek_subs_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="30 kun", callback_data="uzbek_sub_30")],
        [InlineKeyboardButton(text="90 kun", callback_data="uzbek_sub_90")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_telegram")]
    ]
)

# VIEWS MENU
views_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👁️ oddiy ko'rishlar", callback_data="view_normal")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_telegram")]
    ]
)

# INSTAGRAM MENU
instagram_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="👥 Obunachilar", callback_data="ig_followers")],
        [InlineKeyboardButton(text="👍 Likelar", callback_data="ig_likes")],
        [InlineKeyboardButton(text="👁️ Ko'rishlar", callback_data="ig_views")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_smm")]
    ]
)

# INSTAGRAM FOLLOWERS MENU
ig_followers_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Kafolatsiz Subscribers", callback_data="ig_followers_kafolatsiz")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_instagram")]
    ]
)

# INSTAGRAM LIKES MENU
ig_likes_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Oddiy Likelar", callback_data="ig_likes_oddiy")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_instagram")]
    ]
)

# INSTAGRAM VIEWS MENU
ig_views_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Oddiy Ko'rishlar", callback_data="ig_views_oddiy")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_instagram")]
    ]
)

# GAMES MENU
games_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Mobile Legends", callback_data="game_mobile_legends")],
        [InlineKeyboardButton(text="🔫 PUBG Mobile", callback_data="game_pubg_mobile")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
    ]
)

# MOBILE LEGENDS AMOUNTS
ml_amounts_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="11 Diamonds", callback_data="ml_11_diamonds")],
        [InlineKeyboardButton(text="22 Diamonds", callback_data="ml_22_diamonds")],
        [InlineKeyboardButton(text="56 Diamonds", callback_data="ml_56_diamonds")],
        [InlineKeyboardButton(text="86 Diamonds", callback_data="ml_86_diamonds")],
        [InlineKeyboardButton(text="Weekly Diamonds", callback_data="ml_weekly_diamonds")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_games")]
    ]
)

# PUBG MOBILE AMOUNTS
pubg_amounts_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="30 UC", callback_data="pubg_30_uc")],
        [InlineKeyboardButton(text="60 UC", callback_data="pubg_60_uc")],
        [InlineKeyboardButton(text="325 UC", callback_data="pubg_325_uc")],
        [InlineKeyboardButton(text="660 UC", callback_data="pubg_660_uc")],
        [InlineKeyboardButton(text="Premium 1 Month", callback_data="pubg_premium_1m")],
        [InlineKeyboardButton(text="Premium 3 Months", callback_data="pubg_premium_3m")],
        [InlineKeyboardButton(text="Premium 6 Months", callback_data="pubg_premium_6m")],
        [InlineKeyboardButton(text="Premium Plus 1 Month", callback_data="pubg_premium_plus_1m")],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_games")]
    ]
)

# =========================
# SERVICES (FULL)
# =========================
SERVICES = {
    "sub_30":  {"id": "01", "name": "30 kunlik", "price": 0, "min": 100, "max": 10000},
    "sub_60":  {"id": "02", "name": "60 kunlik", "price": 0, "min": 500, "max": 10000},
    "sub_90":  {"id": "03", "name": "90 kunlik", "price": 0, "min": 500, "max": 10000},
    "sub_120": {"id": "04", "name": "120 kunlik", "price": 0, "min": 500, "max": 10000},
    "sub_180": {"id": "05", "name": "180 kunlik", "price": 0, "min": 500, "max": 10000},
    "sub_365": {"id": "06", "name": "365 kunlik", "price": 0, "min": 500, "max": 10000},
    "uzbek_sub_30": {"id": "07", "name": "30 kunlik Uzbek", "price": 0, "min": 100, "max": 10000},
    "uzbek_sub_90": {"id": "08", "name": "90 kunlik Uzbek", "price": 0, "min": 100, "max": 10000},
    "view_normal": {"id": "09", "name": "Oddiy ko'rishlar", "price": 0, "min": 100, "max": 100000},
    "ig_followers_kafolatsiz": {"id": "10", "name": "Instagram Kafolatsiz obunachi", "price": 0, "min": 100, "max": 5000},
    "ig_likes_oddiy": {"id": "11", "name": "Instagram Oddiy Likelar", "price": 0, "min": 100, "max": 5000},
    "ig_views_oddiy": {"id": "12", "name": "Instagram Oddiy Ko'rishlar", "price": 0, "min": 100, "max": 100000},
    "ml_11_diamonds": {"id": "13", "name": "Mobile Legends 11 Diamonds", "price": 1000, "min": 1, "max": 1},
    "ml_22_diamonds": {"id": "14", "name": "Mobile Legends 22 Diamonds", "price": 2000, "min": 1, "max": 1},
    "ml_56_diamonds": {"id": "15", "name": "Mobile Legends 56 Diamonds", "price": 5000, "min": 1, "max": 1},
    "ml_86_diamonds": {"id": "16", "name": "Mobile Legends 86 Diamonds", "price": 8000, "min": 1, "max": 1},
    "ml_weekly_diamonds": {"id": "17", "name": "Mobile Legends Weekly Diamonds", "price": 15000, "min": 1, "max": 1},
    "pubg_30_uc": {"id": "18", "name": "PUBG Mobile 30 UC", "price": 3000, "min": 1, "max": 1},
    "pubg_60_uc": {"id": "19", "name": "PUBG Mobile 60 UC", "price": 6000, "min": 1, "max": 1},
    "pubg_325_uc": {"id": "20", "name": "PUBG Mobile 325 UC", "price": 30000, "min": 1, "max": 1},
    "pubg_660_uc": {"id": "21", "name": "PUBG Mobile 660 UC", "price": 60000, "min": 1, "max": 1},
    "pubg_premium_1m": {"id": "22", "name": "PUBG Mobile Premium 1 Month", "price": 25000, "min": 1, "max": 1},
    "pubg_premium_3m": {"id": "23", "name": "PUBG Mobile Premium 3 Months", "price": 70000, "min": 1, "max": 1},
    "pubg_premium_6m": {"id": "24", "name": "PUBG Mobile Premium 6 Months", "price": 130000, "min": 1, "max": 1},
    "pubg_premium_plus_1m": {"id": "25", "name": "PUBG Mobile Premium Plus 1 Month", "price": 35000, "min": 1, "max": 1},
}

# =========================
# ENTRY
# =========================
@router.message(lambda m: m.text and m.text.strip() == "📢 SMM xizmatlari")
async def smm_entry(message: Message):
    await message.answer("📌 Tanlang:", reply_markup=smm_kb)

@router.message(lambda m: m.text and m.text.strip() == "🎮 O'yinlarga donat")
async def games_entry(message: Message):
    await message.answer("🎮 O'yinlar:", reply_markup=games_kb)

# TELEGRAM
@router.callback_query(F.data == "smm_telegram")
async def tg(call: CallbackQuery):
    await call.message.edit_text("📲 Telegram xizmatlari:", reply_markup=telegram_kb)
    await call.answer()

# INSTAGRAM
@router.callback_query(F.data == "smm_instagram")
async def ig(call: CallbackQuery):
    await call.message.edit_text("📸 Instagram xizmatlari:", reply_markup=instagram_kb)
    await call.answer()

# BACK
@router.callback_query(F.data == "back_to_smm")
async def back_main(call: CallbackQuery):
    await call.message.edit_text("📌 Tanlang:", reply_markup=smm_kb)
    await call.answer()

@router.callback_query(F.data == "back_to_telegram")
async def back_tg(call: CallbackQuery):
    await call.message.edit_text("📲 Telegram xizmatlari:", reply_markup=telegram_kb)
    await call.answer()

@router.callback_query(F.data == "back_to_instagram")
async def back_ig(call: CallbackQuery):
    await call.message.edit_text("📸 Instagram xizmatlari:", reply_markup=instagram_kb)
    await call.answer()

# TELEGRAM SUBSCRIBERS
# OBUNACHI
@router.callback_query(F.data == "tg_subs")
async def subs(call: CallbackQuery):
    await call.message.edit_text("👥 Obunachi tanlang:", reply_markup=subs_kb)
    await call.answer()

# UZBEK OBUNACHI
@router.callback_query(F.data == "uzbek_subs")
async def uzbek_subs(call: CallbackQuery):
    await call.message.edit_text("🇺🇿 Uzbek obunachi tanlang:", reply_markup=uzbek_subs_kb)
    await call.answer()

# VIEWS
@router.callback_query(F.data == "tg_views")
async def views(call: CallbackQuery):
    await call.message.edit_text("👁️ ko'rishlarni tanlang:", reply_markup=views_kb)
    await call.answer()

# INSTAGRAM FOLLOWERS
@router.callback_query(F.data == "ig_followers")
async def ig_followers(call: CallbackQuery):
    await call.message.edit_text("👥 Obunachilar turini tanlang:", reply_markup=ig_followers_kb)
    await call.answer()

# INSTAGRAM LIKES
@router.callback_query(F.data == "ig_likes")
async def ig_likes(call: CallbackQuery):
    await call.message.edit_text("👍 Likelar turini tanlang:", reply_markup=ig_likes_kb)
    await call.answer()

# INSTAGRAM VIEWS
@router.callback_query(F.data == "ig_views")
async def ig_views(call: CallbackQuery):
    await call.message.edit_text("👁️ Ko'rishlar turini tanlang:", reply_markup=ig_views_kb)
    await call.answer()

# GAMES
@router.callback_query(F.data == "smm_games")
async def games_menu(call: CallbackQuery):
    await call.message.edit_text("🎮 O'yinlar:", reply_markup=games_kb)
    await call.answer()

# BACK TO GAMES
@router.callback_query(F.data == "back_to_games")
async def back_games(call: CallbackQuery):
    await call.message.edit_text("🎮 O'yinlar:", reply_markup=games_kb)
    await call.answer()

# MOBILE LEGENDS
@router.callback_query(F.data == "game_mobile_legends")
async def mobile_legends(call: CallbackQuery):
    await call.message.edit_text("🎮 Mobile Legends - Miqdorni tanlang:", reply_markup=ml_amounts_kb)
    await call.answer()

# PUBG MOBILE
@router.callback_query(F.data == "game_pubg_mobile")
async def pubg_mobile(call: CallbackQuery):
    await call.message.edit_text("🔫 PUBG Mobile - Miqdorni tanlang:", reply_markup=pubg_amounts_kb)
    await call.answer()

# =========================
# 📦 SERVICE INFO (MUHIM)
# =========================
@router.callback_query(lambda call: call.data in SERVICES)
async def service_info(call: CallbackQuery):

    service = SERVICES[call.data]
    user_service[call.from_user.id] = call.data

    text = (
        f"📦 XIZMAT MA'LUMOTI\n\n"
        f"🆔 ID: {service['id']}\n"
        f"📛 Nomi: {service['name']}\n"
        f"💰 Narx (1000 ta): {service['price']} so'm\n"
        f"📉 Minimal: {service['min']}\n"
        f"📈 Maksimal: {service['max']}"
    )

    if call.data.startswith("sub_"):
        back_callback = "tg_subs"
    elif call.data.startswith("uzbek_sub_"):
        back_callback = "uzbek_subs"
    elif call.data.startswith("view_"):
        back_callback = "tg_views"
    elif call.data.startswith("ig_followers_"):
        back_callback = "ig_followers"
    elif call.data.startswith("ig_likes_"):
        back_callback = "ig_likes"
    elif call.data.startswith("ig_views_"):
        back_callback = "ig_views"
    elif call.data.startswith("ml_"):
        back_callback = "game_mobile_legends"
    elif call.data.startswith("pubg_"):
        back_callback = "game_pubg_mobile"
    else:
        back_callback = "back_to_smm"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Buyurtma berish", callback_data="order_start")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)]
        ]
    )

    # For games, check balance first
    if call.data.startswith(("ml_", "pubg_")):
        from utils import get_balance
        balance = get_balance(call.from_user.id)
        if balance < service['price']:
            await call.message.edit_text(
                f"❌ Balans yetarli emas!\n\n"
                f"💰 Kerakli: {service['price']} so'm\n"
                f"💰 Mavjud: {balance} so'm",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)]]
                )
            )
            await call.answer()
            return
        
        # Balance sufficient, proceed to ID input
        user_step[call.from_user.id] = "game_id"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)]
            ]
        )
        if call.data.startswith("ml_"):
            await call.message.edit_text(
                f"✅ Balans yetarli!\n\n"
                f"🎮 {service['name']}\n"
                f"💰 Narx: {service['price']} so'm\n\n"
                f"🆔 ID va Zone ID kiriting (xxxxxx(xxxx) formatida):",
                reply_markup=kb
            )
        else:  # PUBG
            await call.message.edit_text(
                f"✅ Balans yetarli!\n\n"
                f"🔫 {service['name']}\n"
                f"💰 Narx: {service['price']} so'm\n\n"
                f"🆔 ID kiriting (xxxxxxxx formatida):",
                reply_markup=kb
            )
        await call.answer()
        return

    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

# =========================
# ORDER START
# =========================
@router.callback_query(F.data == "order_start")
async def start_order(call: CallbackQuery):
    user_step[call.from_user.id] = "qty"
    await call.message.answer("🔢 Miqdorni kiriting:")
    await call.answer()

# =========================
# QTY
# =========================
@router.message(lambda m: m.text and user_step.get(m.from_user.id) == "qty")
async def get_qty(message: Message):

    uid = message.from_user.id

    if user_step.get(uid) != "qty":
        return

    # Check if it's a valid number
    import re
    if not re.match(r'^\d+$', message.text):
        return

    try:
        qty = int(message.text)
        service = SERVICES[user_service[uid]]

        if qty < service["min"] or qty > service["max"]:
            await message.answer(f"❌ {service['min']} - {service['max']} oralig‘ida kiriting")
            return

        user_qty[uid] = qty
        user_step[uid] = "link"

        await message.answer("🔗 Link yuboring:")
    except KeyError:
        await message.answer("❌ Xizmat topilmadi. Qaytadan boshlang.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
    except Exception as e:
        print(f"Error in get_qty: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
        user_qty.pop(uid, None)

# =========================
# LINK
# =========================
@router.message(lambda m: m.text and user_step.get(m.from_user.id) == "link")
async def get_link(message: Message):

    uid = message.from_user.id

    if user_step.get(uid) != "link":
        return

    try:
        user_link[uid] = message.text

        service = SERVICES[user_service[uid]]
        qty = user_qty[uid]

        total = int((qty / 1000) * service["price"])

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_order"),
                    InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_order")
                ]
            ]
        )

        await message.answer(
            f"📦 BUYURTMA\n\n"
            f"🆔 {service['id']}\n"
            f"🔢 {qty}\n"
            f"🔗 {message.text}\n"
            f"💰 {total} so'm",
            reply_markup=kb
        )
    except KeyError:
        await message.answer("❌ Xizmat ma'lumotlari topilmadi. Qaytadan boshlang.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
        user_qty.pop(uid, None)
        user_link.pop(uid, None)
    except Exception as e:
        print(f"Error in get_link: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
        user_qty.pop(uid, None)
        user_link.pop(uid, None)

# GAME ID INPUT
@router.message(lambda m: m.text and user_step.get(m.from_user.id) == "game_id")
async def get_game_id(message: Message):

    uid = message.from_user.id

    if user_step.get(uid) != "game_id":
        return

    try:
        service = SERVICES[user_service[uid]]
        is_ml = service['id'].startswith('ml_')
        
        if is_ml:
            # Mobile Legends: ID(ZoneID) format
            if '(' not in message.text or ')' not in message.text:
                await message.answer(
                    "❌ Noto'g'ri format! ID va Zone ID kiriting (masalan: 123456(7890))"
                )
                return
            
            try:
                game_id_part, zone_part = message.text.split('(')
                zone_id = zone_part.rstrip(')')
                game_id = game_id_part.strip()
                zone_id = zone_id.strip()
                
                # Validate format
                if not game_id.isdigit() or not zone_id.isdigit():
                    raise ValueError
                
                user_game_id[uid] = game_id
                user_game_zone[uid] = zone_id
                
            except ValueError:
                await message.answer(
                    "❌ Noto'g'ri format! Faqat raqamlardan iborat bo'lishi kerak (masalan: 123456(7890))"
                )
                return
        else:
            # PUBG: Just ID
            if not message.text.isdigit():
                await message.answer(
                    "❌ Noto'g'ri format! Faqat raqamlardan iborat ID kiriting (masalan: 12345678)"
                )
                return
            
            user_game_id[uid] = message.text

        # Show confirmation
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_game_order"),
                    InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_game_order")
                ]
            ]
        )

        if is_ml:
            await message.answer(
                f"🎮 MOBILE LEGENDS TOP-UP\n\n"
                f"🆔 ID: {user_game_id[uid]}\n"
                f"🏢 Zone: {user_game_zone[uid]}\n"
                f"🎯 {service['name']}\n"
                f"💰 {service['price']} so'm",
                reply_markup=kb
            )
        else:
            await message.answer(
                f"🔫 PUBG MOBILE TOP-UP\n\n"
                f"🆔 ID: {user_game_id[uid]}\n"
                f"🎯 {service['name']}\n"
                f"💰 {service['price']} so'm",
                reply_markup=kb
            )
            
    except KeyError:
        await message.answer("❌ Xizmat ma'lumotlari topilmadi. Qaytadan boshlang.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
        user_game_id.pop(uid, None)
        user_game_zone.pop(uid, None)
    except Exception as e:
        print(f"Error in get_game_id: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        user_step.pop(uid, None)
        user_service.pop(uid, None)
        user_game_id.pop(uid, None)
        user_game_zone.pop(uid, None)

# CANCEL
@router.callback_query(F.data == "cancel_order")
async def cancel(call: CallbackQuery):
    uid = call.from_user.id
    
    # Clear states
    user_step.pop(uid, None)
    user_service.pop(uid, None)
    user_qty.pop(uid, None)
    user_link.pop(uid, None)
    
    await call.message.answer("❌ Bekor qilindi")
    await call.answer()

# CONFIRM ORDER
@router.callback_query(F.data == "confirm_order")
async def confirm_order(call: CallbackQuery):
    uid = call.from_user.id
    
    service_key = user_service.get(uid)
    qty = user_qty.get(uid)
    link = user_link.get(uid)
    
    if not all([service_key, qty, link]):
        await call.message.answer("❌ Xatolik yuz berdi")
        return
    
    service = SERVICES[service_key]
    total = int((qty / 1000) * service["price"])
    
    # Check balance
    from utils import get_balance
    balance = get_balance(uid)
    
    if balance < total:
        await call.message.answer("❌ Balans yetarli emas")
        return
    
    # Deduct balance
    from utils import update_balance
    from utils import get_or_create_user
    user = get_or_create_user(uid)
    update_balance(user[2], -total)
    
    # Create order
    create_order(uid, service["id"], qty, link, total)
    
    # Send notification to admin
    admin_text = (
        f"🆕 YANGI BUYURTMA!\n\n"
        f"👤 User ID: {user[2]}\n"
        f"🔧 Xizmat: {service['name']} ({service['id']})\n"
        f"🔢 Miqdor: {qty}\n"
        f"🔗 Link: {link}\n"
        f"💰 Summa: {total} so'm\n"
        f"📅 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        await call.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Admin notification failed: {e}")
    
    # Clear state
    user_step.pop(uid, None)
    user_service.pop(uid, None)
    user_qty.pop(uid, None)
    user_link.pop(uid, None)
    
    await call.message.answer("✅ Buyurtma qabul qilindi!")
    await call.answer()

# CANCEL GAME ORDER
@router.callback_query(F.data == "cancel_game_order")
async def cancel_game_order(call: CallbackQuery):
    uid = call.from_user.id
    
    # Clear states
    user_step.pop(uid, None)
    user_service.pop(uid, None)
    user_game_id.pop(uid, None)
    user_game_zone.pop(uid, None)
    
    await call.message.answer("❌ Bekor qilindi")
    await call.answer()

# CONFIRM GAME ORDER
@router.callback_query(F.data == "confirm_game_order")
async def confirm_game_order(call: CallbackQuery):
    uid = call.from_user.id
    
    service_key = user_service.get(uid)
    game_id = user_game_id.get(uid)
    
    if not all([service_key, game_id]):
        await call.message.answer("❌ Xatolik yuz berdi")
        return
    
    service = SERVICES[service_key]
    total = service["price"]
    
    # Check balance
    from utils import get_balance
    balance = get_balance(uid)
    
    if balance < total:
        await call.message.answer("❌ Balans yetarli emas")
        return
    
    # Deduct balance
    from utils import update_balance
    from utils import get_or_create_user
    user = get_or_create_user(uid)
    update_balance(user[2], -total)
    
    # Create order
    is_ml = service['id'].startswith('ml_')
    if is_ml:
        zone_id = user_game_zone.get(uid)
        link = f"{game_id}({zone_id})"
    else:
        link = game_id
    
    create_order(uid, service["id"], 1, link, total)  # qty=1 for games
    
    # Send notification to admin
    if is_ml:
        admin_text = (
            f"🎮 YANGI GAME TOP-UP!\n\n"
            f"👤 User ID: {user[2]}\n"
            f"🎯 O'yin: Mobile Legends\n"
            f"🆔 Game ID: {game_id}\n"
            f"🏢 Zone ID: {zone_id}\n"
            f"💎 {service['name']}\n"
            f"💰 Summa: {total} so'm\n"
            f"📅 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        admin_text = (
            f"🔫 YANGI GAME TOP-UP!\n\n"
            f"👤 User ID: {user[2]}\n"
            f"🎯 O'yin: PUBG Mobile\n"
            f"🆔 Game ID: {game_id}\n"
            f"🎁 {service['name']}\n"
            f"💰 Summa: {total} so'm\n"
            f"📅 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    try:
        await call.bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        print(f"Admin notification failed: {e}")
    
    # Clear state
    user_step.pop(uid, None)
    user_service.pop(uid, None)
    user_game_id.pop(uid, None)
    user_game_zone.pop(uid, None)
    
    await call.message.answer("✅ Top-up buyurtma qabul qilindi!")
    await call.answer()
