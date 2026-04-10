import asyncio
import aiosqlite
import os
from database import DB_PATH, init_db

RON_TO_LTC_RATE = 250.0

async def seed_data():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        # Full reset
        await db.execute("DELETE FROM item_images")
        await db.execute("DELETE FROM items")
        await db.execute("DELETE FROM categories")
        await db.execute("DELETE FROM sales")
        await db.execute("DELETE FROM preorders")
        await db.commit()
        await db.execute("VACUUM")

        # Define 9 categories with precise emojis
        # Order: ☘️, ❄️, 🍫, 🍬, 🍾, 🏃, 🐎, 💎, 🔮
        categories_data = [
            {"id": 1, "emoji": "❄️", "desc": "Zăpada de la Polul Nord. MOG-GRADE CRYSTAL for intense status.", "img": "assets/cocos.jpg"},
            {"id": 2, "emoji": "🐎", "desc": "Putere de cal sălbatic. ELITE MOGGER ENERGY. Trece prin ziduri ca un boss.", "img": "assets/kaluti.jpg"},
            {"id": 3, "emoji": "☘️", "desc": "Gazon de elită ELITA LUX. VIBE MAXIM, MOG-LEVEL: GOD. @sagagaubackup for elite support.", "img": "assets/gazon.jpg"},
            {"id": 4, "emoji": "🍾", "desc": "Medeul de AUR PUR. Porți asta și toată lumea e mogged. MAX MOGGING VIBE.", "img": "assets/medalion.jpg"},
            {"id": 5, "emoji": "🍬", "desc": "Diamantele visătorilor MOG-DIAMONDS. Mica, dar te mută din loc direct în top.", "img": "assets/bb.jpg"},
            {"id": 6, "emoji": "🏃", "desc": "Turbo pe bune ELITE PERFORMANCE. Dai în ele și îi moggezi pe toți la viteză.", "img": "assets/viteza.jpg"},
            {"id": 7, "emoji": "🍫", "desc": "Ciocolată de aia fină, să-ți ungă sufletul de mogger.", "img": "assets/shop.png"},
            {"id": 8, "emoji": "🔮", "desc": "Fără control total. MOG-TRANSFORMATION. Vezi succesul pur în oglindă.", "img": "assets/carton.jpg"},
            {"id": 9, "emoji": "💎", "desc": "Vedere 4K MOG-VISION. Vezi viitorul, vezi succesul, vezi cum îi moggezi pe restul.", "img": "assets/cristi.jpg"}
        ]

        for cat in categories_data:
            await db.execute(
                "INSERT INTO categories (id, name, description, display_image) VALUES (?, ?, ?, ?)",
                (cat["id"], cat["emoji"], cat["desc"], cat["img"])
            )

        # Precise Item Lists from User Request
        items_payload = {
            1: [(1, 500), (2, 900), (5, 2000), (10, 3650), (20, 7000)], # COCOS
            2: [(1, 200), (2, 300), (5, 600), (10, 1000), (30, 2400), (50, 3500), (100, 6000)], # KALUTI
            3: [(2, 100), (5, 200), (10, 375), (20, 700), (30, 1000), (50, 1500), (100, 2800)], # GAZON
            4: [(1, 200), (2, 300), (5, 600), (10, 1000), (30, 2400), (50, 3500), (100, 6000)], # MEDALION
            5: [(2, 100), (5, 200), (10, 375), (20, 700), (30, 1000), (50, 1400), (100, 2500)], # BB
            6: [(1, 100), (2, 200), (5, 400), (10, 700), (20, 1200), (30, 1600), (50, 2250), (100, 3700)], # VITEZA
            7: [(2, 100), (5, 225), (10, 400), (20, 700), (30, 1000), (50, 1500), (100, 2750)], # CHOCOLATE
            8: [(1, 100), (5, 400), (10, 700), (20, 1200), (30, 1500), (50, 2250), (100, 3250)], # CRISTAL
            9: [(1, 200), (2, 300), (5, 600), (10, 1000), (30, 2400), (50, 3000), (100, 5000)]  # DIAMANT
        }

        # Map ID to Emoji for item names
        emoji_map = {c["id"]: c["emoji"] for c in categories_data}

        for cat_id, prices in items_payload.items():
            emoji = emoji_map[cat_id]
            for qty, price_ron in prices:
                item_name = f"{emoji} {qty} = {price_ron} RON"
                price_ltc = round(price_ron / RON_TO_LTC_RATE, 4)
                
                cursor = await db.execute(
                    "INSERT INTO items (category_id, name, description, price_ron, price_ltc, is_primary) VALUES (?, ?, ?, ?, ?, 1)",
                    (cat_id, item_name, f"Calitate premium garantată pentru {item_name}.", float(price_ron), price_ltc)
                )
                item_id = cursor.lastrowid
                
                # STOCK IS NOW EMPTY BY DEFAULT
                # You can add stock for specific items manually to make them '🟢'


        await db.commit()
        print("DATABASE SUCCESSFULLY RESET AND SEEDED WITH ENCODING-SAFE SCRIPT!")

if __name__ == "__main__":
    asyncio.run(seed_data())
