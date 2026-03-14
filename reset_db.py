import asyncio
import aiosqlite
from database import DB_PATH, init_db

# 1 LTC = 300 RON (Using a slightly higher rate for safety/rounding, or user can adjust)
RON_TO_LTC_RATE = 280.0 

async def reset_and_seed():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DROP TABLE IF EXISTS sales")
        await db.execute("DROP TABLE IF EXISTS item_images")
        await db.execute("DROP TABLE IF EXISTS items")
        await db.execute("DROP TABLE IF EXISTS categories")
        await db.commit()
        await db.execute("VACUUM")
    
    await init_db()
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Category Names are Emojis
        categories_data = [
            ("❄️", "https://i.imgur.com/8HOn7jN.png"),
            ("🐎", "https://i.imgur.com/8HOn7jN.png"),
            ("☘️", "https://i.imgur.com/8HOn7jN.png"),
            ("🍾", "https://i.imgur.com/8HOn7jN.png"),
            ("🍬", "https://i.imgur.com/8HOn7jN.png"),
            ("🏃", "https://i.imgur.com/8HOn7jN.png"),
            ("🍫", "https://i.imgur.com/8HOn7jN.png"),
            ("🔮", "https://i.imgur.com/8HOn7jN.png"),
            ("💎", "https://i.imgur.com/8HOn7jN.png")
        ]
        
        for emoji, img in categories_data:
            await db.execute("INSERT INTO categories (name, display_image) VALUES (?, ?)", (emoji, img))
        
        async with db.execute("SELECT id, name FROM categories") as cursor:
            cat_rows = await cursor.fetchall()
            cat_map = {name: id for id, name in cat_rows}
            
        # Naming pattern: 1x[EMOJI] = [PRICE] RON
        # Price lists provided by user:
        # ❄️: 1-500, 2-900, 5-2000, 10-3650, 20-7000
        # 🐎: 1-200, 2-300, 5-600, 10-1000, 30-2400, 50-3500, 100-6000
        # ☘️: 2-100, 5-200, 10-375, 20-700, 30-1000, 50-1500, 100-2800
        
        price_structures = {
            "❄️": [(1, 500), (2, 900), (5, 2000)],
            "🐎": [(1, 200), (2, 300), (5, 600)],
            "☘️": [(2, 100), (5, 200), (10, 375)],
            "🍾": [(1, 200), (2, 300), (5, 600)],
            "🍬": [(2, 100), (5, 200), (10, 375)],
            "🏃": [(1, 100), (2, 200), (5, 400), (10, 700)],
            "🍫": [(2, 100), (5, 225), (10, 400)],
            "🔮": [(1, 100), (5, 400), (10, 700)],
            "💎": [(1, 200), (2, 300), (5, 600)]
        }
        
        for emoji, tiers in price_structures.items():
            cat_id = cat_map[emoji]
            for qty, price_ron in tiers:
                item_name = f"{qty}x{emoji} = {price_ron} RON"
                price_ltc = round(price_ron / RON_TO_LTC_RATE, 4)
                
                # Insert item
                cursor = await db.execute(
                    "INSERT INTO items (category_id, name, description, price_ron, price_ltc, display_image) VALUES (?, ?, ?, ?, ?, ?)",
                    (cat_id, item_name, f"Achiziționează {qty} unități de {emoji}. Livrare instant.", price_ron, price_ltc, categories_data[0][1])
                )
                item_id = cursor.lastrowid
                
                # Add sample stock for 1st tier only to show red/green difference
                if tiers.index((qty, price_ron)) == 0:
                    for i in range(3):
                        await db.execute(
                            "INSERT INTO item_images (item_id, image_url) VALUES (?, ?)",
                            (item_id, f"STOC_{emoji}_{qty}_{i}")
                        )
        
        await db.commit()
    print("Database Reset & Seeding with User Patterns Complete!")

if __name__ == "__main__":
    asyncio.run(reset_and_seed())
