import sqlite3

conn = sqlite3.connect('sale_tracker.db')
cursor = conn.cursor()

# Search for Cruiser items
items = cursor.execute("""
    SELECT title, price, original_price, discount, url 
    FROM sale_items 
    WHERE LOWER(title) LIKE '%cruiser%' 
    OR LOWER(title) LIKE '%tin cloth%'
    ORDER BY title
""").fetchall()

print("Found Cruiser/Tin Cloth items:")
for item in items:
    title, price, original_price, discount, url = item
    print(f"  Title: {title}")
    print(f"  Price: {price}")
    print(f"  Original Price: {original_price}")
    print(f"  Discount: {discount}")
    print(f"  URL: {url}")
    print("  " + "-"*50)

# Also check if there are any items with missing price data
print("\nItems with missing price data (first 10):")
missing_price = cursor.execute("""
    SELECT title, url
    FROM sale_items 
    WHERE price IS NULL OR original_price IS NULL
    LIMIT 10
""").fetchall()

for item in missing_price:
    print(f"  {item[0]} - {item[1]}")

conn.close()