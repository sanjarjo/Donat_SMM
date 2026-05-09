import sqlite3

DB_NAME = "bot.db"


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        user_code TEXT UNIQUE,
        balance INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        service_id TEXT,
        qty INTEGER,
        link TEXT,
        amount INTEGER,
        status TEXT,
        created_at TEXT
    )
    """)

    # FIX: Narxlarni DB da saqlash uchun yangi table
    # Restart bo'lganda narxlar yo'qolmaydi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_prices (
        service_key TEXT PRIMARY KEY,
        price INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def get_or_create_user(tg_id: int):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    user = cursor.fetchone()

    if user:
        conn.close()
        return user

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0] + 1
    user_code = str(count).zfill(5)

    cursor.execute(
        "INSERT INTO users (tg_id, user_code, balance) VALUES (?, ?, ?)",
        (tg_id, user_code, 0)
    )
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    new_user = cursor.fetchone()
    conn.close()
    return new_user


def get_user_by_code(user_code: str):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_code=?", (user_code,))
    user = cursor.fetchone()
    conn.close()
    return user


def update_balance(user_code: str, amount: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_code=?",
        (amount, user_code)
    )
    conn.commit()
    conn.close()


def get_balance(tg_id: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE tg_id=?", (tg_id,))
    result = cursor.fetchone()
    conn.close()
    return result["balance"] if result else 0


# ========================
# FIX: Narxlarni DB da saqlash/olish
# ========================
def save_service_price(service_key: str, price: int):
    """Narxni DB ga saqlaydi (restart'dan keyin ham saqlanadi)"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO service_prices (service_key, price)
        VALUES (?, ?)
        ON CONFLICT(service_key) DO UPDATE SET price=excluded.price
    """, (service_key, price))
    conn.commit()
    conn.close()


def load_service_prices() -> dict:
    """DB dan barcha narxlarni yuklaydi"""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT service_key, price FROM service_prices")
    rows = cursor.fetchall()
    conn.close()
    return {row["service_key"]: row["price"] for row in rows}
    
