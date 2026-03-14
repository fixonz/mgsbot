import sqlite3
import os

db_path = 'bot_database.sqlite'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Ensure category 6 name has emoji
cursor.execute("UPDATE categories SET name = '🏃' WHERE id = 6")

# 2. Check items in category 6
cursor.execute("SELECT id, name, price_ron FROM items WHERE category_id = 6")
items = cursor.fetchall()
print(f"Current items in category 6: {len(items)}")

has_200 = False
for item_id, name, price in items:
    print(f"Item {item_id}: {name} ({price} RON)")
    if price == 200:
        has_200 = True
        # Ensure it has the emoji
        if '🏃' not in name:
            new_name = f"🏃 2 = 200 RON"
            cursor.execute("UPDATE items SET name = ? WHERE id = ?", (new_name, item_id))
            print(f"Updated item {item_id} name to {new_name}")

if not has_200:
    print("Adding 2 = 200 RON item...")
    rate = 250.0
    price_ron = 200.0
    price_ltc = round(price_ron / rate, 4)
    item_name = '🏃 2 = 200 RON'
    desc = f"Calitate premium garantată pentru {item_name}."
    cursor.execute("INSERT INTO items (category_id, name, description, price_ron, price_ltc) VALUES (6, ?, ?, ?, ?)", 
                   (item_name, desc, price_ron, price_ltc))

# 3. Double check ALL items in category 6 have the runner emoji
cursor.execute("SELECT id, name FROM items WHERE category_id = 6")
for item_id, name in cursor.fetchall():
    if not name.startswith('🏃'):
        # Fix name format if it's like "1 = 100 RON" without emoji
        if " = " in name:
            new_name = f"🏃 {name}"
        else:
            # Fallback
            new_name = f"🏃 {name}"
        cursor.execute("UPDATE items SET name = ? WHERE id = ?", (new_name, item_id))
        print(f"Fixed emoji for item {item_id}: {new_name}")

conn.commit()
conn.close()
print("Database update complete.")
