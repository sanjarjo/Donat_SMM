from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import main_menu
from config import ADMIN_ID
from utils import get_or_create_user
import re

router = Router()

# STATE - Scoped per user, not shared with admin panel
# User mode tracking: "payment_atm", "payment_p2p", None
user_payment_mode = {}
awaiting_check = {}
attempts = {}
awaiting_p2p_amount = {}
awaiting_p2p_check = {}
p2p_amount = {}

@router.callback_query(F.data == "payment_atm")
async def payment_atm(call: CallbackQuery):
    uid = call.from_user.id
    # Set mode to ATM payment and clear any conflicting state
    user_payment_mode[uid] = "payment_atm"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 To'lash", callback_data="confirm_payment"),
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")
            ]
        ]
    )
    
    text = (
        "🏦 ATM orqali to'lov\n\n"
        "💳 Karta raqami: 9860 0827 1937 9966\n\n"
        "📝 Raqamingizni kiriting va chekni rasm ko'rinishida yuboring.\n\n"
        "⚠️ Faqat rasm formatida yuboring!"
    )
    
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "confirm_payment")
async def confirm_payment(call: CallbackQuery):
    uid = call.from_user.id
    user_payment_mode[uid] = "payment_atm"
    awaiting_check[uid] = True
    attempts[uid] = 0
    
    await call.message.edit_text(
        "📸 Chek rasmini yuboring:\n\n"
        "⚠️ Faqat rasm formatida yuboring!"
    )
    await call.answer()

@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(call: CallbackQuery):
    await call.message.answer("❌ Bekor qilindi", reply_markup=main_menu)
    await call.answer()

# ADMIN ORQALI
@router.callback_query(F.data == "payment_admin")
async def payment_admin(call: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
        ]
    )
    
    await call.message.edit_text(
        "👨‍💼 Admin bilan bog'laning: @sanjar7729",
        reply_markup=kb
    )
    await call.answer()

# BACK TO MAIN
@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: CallbackQuery):
    uid = call.from_user.id
    # Clear ALL payment-related state
    awaiting_check.pop(uid, None)
    attempts.pop(uid, None)
    awaiting_p2p_amount.pop(uid, None)
    awaiting_p2p_check.pop(uid, None)
    p2p_amount.pop(uid, None)
    user_payment_mode.pop(uid, None)

    await call.message.answer("Bosh menyu", reply_markup=main_menu)
    await call.answer()

# P2P
@router.callback_query(F.data == "payment_p2p")
async def payment_p2p(call: CallbackQuery):
    uid = call.from_user.id
    user_payment_mode[uid] = "payment_p2p"
    awaiting_p2p_amount[uid] = True
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
        ]
    )
    
    await call.message.edit_text(
        "💰 Miqdorni kiriting (faqat raqamlar):",
        reply_markup=kb
    )
    await call.answer()

# GET P2P AMOUNT
@router.message(lambda m: m.text and m.from_user.id and awaiting_p2p_amount.get(m.from_user.id))
async def get_p2p_amount(message: Message):
    uid = message.from_user.id
    
    # Extra safety check: ensure we're in P2P mode
    if user_payment_mode.get(uid) != "payment_p2p":
        return
    
    if not re.match(r'^\d+$', message.text):
        await message.answer("❌ Faqat raqam kiriting!")
        return
    
    amount = int(message.text)
    if amount <= 0:
        await message.answer("❌ Miqdor 0 dan katta bo'lishi kerak!")
        return
    
    p2p_amount[uid] = amount
    awaiting_p2p_amount.pop(uid, None)
    awaiting_p2p_check[uid] = True
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_main")]
        ]
    )
    
    await message.answer(
        f"💳 Karta raqami: 9860 0827 1937 9966\n"
        f"👤 Ism familiya: M.Ch\n\n"
        f"💰 Miqdor: {amount} so'm\n\n"
        f"📸 Chek rasmini yuboring (faqat rasm):",
        reply_markup=kb
    )

# HANDLE P2P CHECK PHOTO
@router.message(lambda m: m.photo and m.from_user.id and awaiting_p2p_check.get(m.from_user.id))
async def handle_p2p_check(message: Message):
    uid = message.from_user.id
    
    # Safety check: ensure we're in P2P payment mode
    if user_payment_mode.get(uid) != "payment_p2p":
        return
    
    user = get_or_create_user(uid)
    user_code = user[2]
    amount = p2p_amount.get(uid)
    username = message.from_user.username or "Noma'lum"
    from datetime import datetime
    time_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Send to admin
    try:
        await message.bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"💰 P2P to'lov cheki\n👤 User ID: {user_code}\n💵 Miqdor: {amount} so'm\n👤 Username: @{username}\n📅 Vaqt: {time_date}"
        )
    except Exception as e:
        print(f"Failed to send P2P photo to admin: {e}")
    
    # Clear states
    awaiting_p2p_check.pop(uid, None)
    p2p_amount.pop(uid, None)
    user_payment_mode.pop(uid, None)
    
    await message.answer(
        "✅ Chek qabul qilindi!\n\n💰 Balansingiz tez orada to'ldiriladi.",
        reply_markup=main_menu
    )

# INVALID P2P INPUT
@router.message(lambda m: (m.text or m.document or m.audio or m.video or m.voice or m.sticker or m.animation) and m.from_user.id and awaiting_p2p_check.get(m.from_user.id))
async def handle_invalid_p2p_check(message: Message):
    uid = message.from_user.id
    
    if not awaiting_p2p_check.get(uid):
        return
    
    # Ensure we're in P2P mode
    if user_payment_mode.get(uid) != "payment_p2p":
        return
    
    await message.answer(
        "❌ Faqat rasm yuboring!\n\n"
        "📸 Chek rasmini yuboring:"
    )

# CANCEL P2P
@router.callback_query(F.data == "cancel_p2p")
async def cancel_p2p(call: CallbackQuery):
    uid = call.from_user.id
    awaiting_p2p_amount.pop(uid, None)
    awaiting_p2p_check.pop(uid, None)
    p2p_amount.pop(uid, None)
    user_payment_mode.pop(uid, None)
    
    await call.message.answer("❌ Bekor qilindi", reply_markup=main_menu)
    await call.answer()

@router.message(lambda m: m.photo and m.from_user.id and awaiting_check.get(m.from_user.id))
async def handle_check_photo(message: Message):
    uid = message.from_user.id
    
    if not awaiting_check.get(uid):
        return
    
    # Safety check: ensure we're in ATM payment mode
    if user_payment_mode.get(uid) != "payment_atm":
        return
    
    # Send photo to admin
    try:
        await message.bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"💰 Yangi to'lov cheki\n👤 User ID: {uid}"
        )
    except Exception as e:
        print(f"Failed to send photo to admin: {e}")
    
    # Clear state
    awaiting_check.pop(uid, None)
    attempts.pop(uid, None)
    user_payment_mode.pop(uid, None)
    
    await message.answer(
        "✅ Chek qabul qilindi!\n\n"
        "💰 Balansingiz tez orada to'ldiriladi.",
        reply_markup=main_menu
    )

@router.message(lambda m: (m.text or m.document or m.audio or m.video or m.voice or m.sticker or m.animation) and m.from_user.id and awaiting_check.get(m.from_user.id))
async def handle_invalid_check(message: Message):
    uid = message.from_user.id
    
    if not awaiting_check.get(uid):
        return
    
    # Ensure we're in ATM payment mode
    if user_payment_mode.get(uid) != "payment_atm":
        return
    
    await message.answer(
        "❌ Faqat rasm yuboring!\n\n"
        "📸 Chek rasmini yuboring:"
    )
    
    attempts[uid] = attempts.get(uid, 0) + 1
    
    if attempts[uid] >= 5:
        awaiting_check.pop(uid, None)
        attempts.pop(uid, None)
        await message.answer(
            "❌ Juda ko'p urinishlar!\n\n"
            "Bosh menyuga qaytarildi.",
            reply_markup=main_menu
        )
        return
    
    remaining = 5 - attempts[uid]
    
    await message.answer(
        f"❌ Faqat rasm yuboring!\n\n"
        f"⚠️ Qolgan urinishlar: {remaining}\n\n"
        "📸 Chek rasmini yuboring:"
    )
