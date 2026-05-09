import sqlite3

def create_orders_table():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()

# Create users table
def create_users_table():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        user_code TEXT UNIQUE,
        balance INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()

# Call it to ensure tables exist
create_orders_table()
create_users_table()