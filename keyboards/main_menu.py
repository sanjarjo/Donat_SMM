from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Oddiy foydalanuvchilar uchun
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Mening hisobim")],
        [KeyboardButton(text="📢 SMM xizmatlari")],
        [KeyboardButton(text="🎮 O'yinlarga donat")],
        [KeyboardButton(text="💰 Hisobni to'ldirish")],
        [KeyboardButton(text="📦 Buyurtmalarim")]
    ],
    resize_keyboard=True
)

# Admin uchun (admin panel tugmasi qo'shilgan)
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Mening hisobim")],
        [KeyboardButton(text="📢 SMM xizmatlari")],
        [KeyboardButton(text="🎮 O'yinlarga donat")],
        [KeyboardButton(text="💰 Hisobni to'ldirish")],
        [KeyboardButton(text="📦 Buyurtmalarim")],
        [KeyboardButton(text="👨‍💼 Admin panel")]  # Faqat admin ko'radi
    ],
    resize_keyboard=True
)

def get_menu(user_id: int, admin_id: int) -> ReplyKeyboardMarkup:
    """User admin bo'lsa admin_menu, aks holda main_menu qaytaradi"""
    return admin_menu if user_id == admin_id else main_menu
    
