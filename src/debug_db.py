#!/usr/bin/env python3
"""Quick database debugging script."""

import sqlite3
from collections import Counter

# Connect directly to the database
conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get discounted items with the same query as the app
cursor.execute('''
    SELECT *, 
           CASE 
               WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
               THEN ROUND(((original_price - price) / original_price) * 100, 1)
               ELSE 0
           END as discount_percent,
           CASE 
               WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
               THEN ROUND(original_price - price, 2)
               ELSE 0
           END as savings_amount
    FROM sale_items 
    WHERE (original_price > price AND price IS NOT NULL AND original_price IS NOT NULL)
       OR (discount IS NOT NULL AND discount != '')
    ORDER BY discount_percent DESC, savings_amount DESC
    LIMIT 100
''')

items = [dict(row) for row in cursor.fetchall()]
urls = [item['url'] for item in items if item['url']]

print(f'Total discounted items: {len(items)}')
print(f'Items with URLs: {len(urls)}')
unique_urls = set(urls)
print(f'Unique URLs: {len(unique_urls)}')
print()

# Show URL frequency
url_counts = Counter(urls)
print('Most common URLs:')
for url, count in url_counts.most_common()[:10]:
    print(f'{count}x: {url[:80]}...')

print()
print('Sample items for most duplicated URL:')
most_common_url = url_counts.most_common(1)[0][0]
sample_items = [item for item in items if item['url'] == most_common_url][:3]
for item in sample_items:
    title = item['title']
    price = item['price']
    orig_price = item['original_price']
    print(f"  - {title} (${price} vs ${orig_price})")

print()
print('Look at Cooper Lake Trunks specifically:')
cursor.execute('''
    SELECT title, url, price, original_price
    FROM sale_items 
    WHERE title LIKE '%Cooper Lake%' 
    ORDER BY title
    LIMIT 20
''')

cooper_items = cursor.fetchall()
for item in cooper_items:
    title = item['title']
    url = item['url'] if item['url'] else 'None'
    price = item['price']
    orig_price = item['original_price']
    print(f"  {title} -> {url[:60]}... (${price} vs ${orig_price})")

conn.close()
