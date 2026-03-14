import aiosqlite
import logging

DB_PATH = "bot_database.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories table (Max 9 logically handled in code)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                display_image TEXT DEFAULT NULL,
                description TEXT DEFAULT NULL
            )
        ''')

        # Items table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                description TEXT,
                price_ron REAL,
                price_ltc REAL,
                display_image TEXT DEFAULT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Item Images / Stock table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS item_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                image_url TEXT,
                is_sold BOOLEAN DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items (id)
            )
        ''')
        
        # Sales Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                image_id INTEGER DEFAULT NULL,
                amount_expected REAL,
                amount_paid REAL DEFAULT 0,
                address_used TEXT,
                tx_hash TEXT UNIQUE DEFAULT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (item_id) REFERENCES items (id),
                FOREIGN KEY (image_id) REFERENCES item_images (id)
            )
        ''')
        
        # Addresses Pool Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crypto_address TEXT UNIQUE,
                in_use_by_sale_id INTEGER DEFAULT NULL,
                locked_until TIMESTAMP DEFAULT NULL
            )
        ''')

        # Preorders Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS preorders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (item_id) REFERENCES items (id)
            )
        ''')

        # Migrations
        try:
            await db.execute("ALTER TABLE categories ADD COLUMN description TEXT DEFAULT NULL")
        except: pass
        try:
            await db.execute("ALTER TABLE sales ADD COLUMN tx_hash TEXT UNIQUE DEFAULT NULL")
        except: pass

        
        await db.commit()

        logging.info("Database initialized successfully.")

# --- Repository functions ---

async def get_available_address(timeout_minutes: int):
    """
    Finds an address that is not in use or whose lock has expired.
    Returns (address, sale_id_to_clear_if_any)
    """
    from datetime import datetime, timedelta
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    async with aiosqlite.connect(DB_PATH) as db:
        # 1. Look for a truly free address
        async with db.execute("SELECT crypto_address FROM addresses WHERE in_use_by_sale_id IS NULL LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0], None
        
        # 2. Look for an address whose lock expired
        async with db.execute("SELECT crypto_address, in_use_by_sale_id FROM addresses WHERE locked_until < ? LIMIT 1", (now_str,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0], row[1]
                
    return None, None

async def create_sale(user_id: int, item_id: int, amount: float, address: str, timeout_minutes: int):
    from datetime import datetime, timedelta
    now = datetime.now()
    expires_at = now + timedelta(minutes=timeout_minutes)
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Create sale
        cursor = await db.execute(
            "INSERT INTO sales (user_id, item_id, amount_expected, address_used, created_at, status) VALUES ((SELECT id FROM users WHERE telegram_id=?), ?, ?, ?, ?, 'pending')",
            (user_id, item_id, amount, address, now_str)
        )
        sale_id = cursor.lastrowid
        
        # Lock address
        await db.execute(
            "UPDATE addresses SET in_use_by_sale_id = ?, locked_until = ? WHERE crypto_address = ?",
            (sale_id, expires_str, address)
        )
        await db.commit()
        return sale_id

async def seed_addresses(addresses_list: list):
    async with aiosqlite.connect(DB_PATH) as db:
        for addr in addresses_list:
            await db.execute("INSERT OR IGNORE INTO addresses (crypto_address) VALUES (?)", (addr,))
        await db.commit()

async def add_user(telegram_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        await db.commit()


