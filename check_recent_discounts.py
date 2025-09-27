import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('sale_tracker.db')
cursor = conn.cursor()

# Check recent items (last hour)
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

recent_items = cursor.execute("""
    SELECT title, price, original_price, discount, url, scraped_at
    FROM sale_items 
    WHERE scraped_at > ? 
    ORDER BY scraped_at DESC
    LIMIT 20
""", (one_hour_ago,)).fetchall()

print(f"Recent items scraped since {one_hour_ago}:")
print()

for item in recent_items:
    title, price, original_price, discount, url, scraped_at = item
    print(f"Title: {title}")
    print(f"Price: ${price}" if price else "Price: Not found")
    print(f"Original Price: ${original_price}" if original_price else "Original Price: None")
    print(f"Discount: {discount}" if discount else "Discount: None")
    print(f"Scraped: {scraped_at}")
    
    if price and original_price and original_price > price:
        discount_pct = ((original_price - price) / original_price) * 100
        savings = original_price - price
        print(f"🔥 CALCULATED DISCOUNT: {discount_pct:.1f}% off (Save ${savings:.2f})")
    
    print("  " + "-" * 60)

# Also check if any items have original_price set at all
any_with_original = cursor.execute("""
    SELECT COUNT(*) FROM sale_items WHERE original_price IS NOT NULL AND original_price > 0
""").fetchone()[0]

print(f"\nTotal items with original price data: {any_with_original}")

conn.close()