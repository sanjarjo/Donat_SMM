from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from keyboards.main_menu import get_menu
from utils import get_or_create_user
from config import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    get_or_create_user(message.from_user.id)

    # Admin bo'lsa admin_menu, aks holda main_menu
    menu = get_menu(message.from_user.id, ADMIN_ID)

    await message.answer(
        "Botga xush kelibsiz 👋",
        reply_markup=menu
    )


@router.message(F.text == "👤 Mening hisobim")
async def account_handler(message: Message):
    user = get_or_create_user(message.from_user.id)

    user_code = user[2]
    balance = user[3]

    await message.answer(
        f"👤 Hisob ma'lumotlari:\n\n"
        f"🆔 ID: {user_code}\n"
        f"💰 Balans: {balance} so'm"
    )


@router.message(F.text == "💰 Hisobni to'ldirish")
async def replenish_handler(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏦 ATM", callback_data="payment_atm")],
            [InlineKeyboardButton(text="👨‍💼 Admin orqali", callback_data="payment_admin")],
            [InlineKeyboardButton(text="💳 P2P", callback_data="payment_p2p")]
        ]
    )

    await message.answer(
        "💰 To'lov turini tanlang:",
        reply_markup=kb
    )
    
