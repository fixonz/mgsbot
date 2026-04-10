import asyncio
import aiosqlite
from database import DB_PATH

async def check():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM categories") as cursor:
            rows = await cursor.fetchall()
            print("CATEGORIES IN DB:")
            for r in rows:
                print(r)
        async with db.execute("SELECT COUNT(*) FROM items") as cursor:
            count = (await cursor.fetchone())[0]
            print(f"TOTAL ITEMS: {count}")

if __name__ == '__main__':
    asyncio.run(check())
