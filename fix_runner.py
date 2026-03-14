import sqlite3
import os

db_path = 'bot_database.sqlite'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- CATEGORIES ---")
cursor.execute("SELECT id, name FROM categories")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}")

print("\n--- ITEMS IN CATEGORY 6 ---")
cursor.execute("SELECT id, name, price_ron FROM items WHERE category_id = 6 ORDER BY price_ron")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Price: {row[2]}")

# Check for missing emoji in category 6
cursor.execute("SELECT name FROM categories WHERE id = 6")
cat_name = cursor.fetchone()[0]
if not cat_name or '🏃' not in cat_name:
    print("\nFixing Category 6 name...")
    cursor.execute("UPDATE categories SET name = '🏃' WHERE id = 6")

# Check if 2 = 200 exists
cursor.execute("SELECT id FROM items WHERE category_id = 6 AND price_ron = 200")
if not cursor.fetchone():
    print("\nAdding 2 = 200 item...")
    # Get current rate or use default
    rate = 250.0 # From seed_data
    price_ron = 200.0
    price_ltc = round(price_ron / rate, 4)
    item_name = '🏃 2 = 200 RON'
    desc = f"Calitate premium garantată pentru {item_name}."
    cursor.execute("INSERT INTO items (category_id, name, description, price_ron, price_ltc) VALUES (6, ?, ?, ?, ?)", 
                   (item_name, desc, price_ron, price_ltc))

conn.commit()
conn.close()
print("\nDone")
