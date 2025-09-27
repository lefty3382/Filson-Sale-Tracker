#!/usr/bin/env python3
"""Compare old vs new scraped data."""

import sqlite3
from collections import Counter

conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get recent data (last hour) with valid prices
cursor.execute('''
    SELECT title, price, original_price, url, scraped_at,
           CASE 
               WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
               THEN ROUND(((original_price - price) / original_price) * 100, 1)
               ELSE 0
           END as discount_percent
    FROM sale_items 
    WHERE scraped_at >= datetime('now', '-1 hour')
    AND original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
    ORDER BY discount_percent DESC
''')

recent_items = cursor.fetchall()
recent_urls = [item['url'] for item in recent_items if item['url']]
recent_unique_urls = set(recent_urls)

print(f'Recent data (last hour):')
print(f'  Total items: {len(recent_items)}')
print(f'  Unique URLs: {len(recent_unique_urls)}')

# Get older data with valid prices  
cursor.execute('''
    SELECT title, price, original_price, url, scraped_at,
           CASE 
               WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
               THEN ROUND(((original_price - price) / original_price) * 100, 1)
               ELSE 0
           END as discount_percent
    FROM sale_items 
    WHERE scraped_at < datetime('now', '-1 hour')
    AND original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
    ORDER BY discount_percent DESC
    LIMIT 100
''')

older_items = cursor.fetchall()
older_urls = [item['url'] for item in older_items if item['url']]
older_unique_urls = set(older_urls)

print(f'Older data (before last hour):')
print(f'  Total items: {len(older_items)}')
print(f'  Unique URLs: {len(older_unique_urls)}')

# Check overlap
overlap = recent_unique_urls & older_unique_urls
print(f'URL overlap: {len(overlap)} URLs appear in both datasets')

# Show what the current get_discounted_items query returns
cursor.execute('''
    SELECT title, price, original_price, url, scraped_at,
           CASE 
               WHEN original_price > price AND price IS NOT NULL AND original_price IS NOT NULL
               THEN ROUND(((original_price - price) / original_price) * 100, 1)
               ELSE 0
           END as discount_percent
    FROM sale_items 
    WHERE (original_price > price AND price IS NOT NULL AND original_price IS NOT NULL)
       OR (discount IS NOT NULL AND discount != '')
    ORDER BY discount_percent DESC
    LIMIT 100
''')

all_items = cursor.fetchall()
all_urls = [item['url'] for item in all_items if item['url']]
all_unique_urls = set(all_urls)

print(f'Current query results:')
print(f'  Total items: {len(all_items)}')
print(f'  Unique URLs: {len(all_unique_urls)}')

# Show first 10 unique URLs from the current query
print(f'\\nFirst 10 unique products from current query:')
seen_urls = set()
for item in all_items:
    url = item['url']
    if url and url not in seen_urls:
        seen_urls.add(url)
        title = item['title']
        price = item['price']
        orig = item['original_price']  
        disc = item['discount_percent']
        print(f'{len(seen_urls):2d}. {title[:50]} - ${price} (was ${orig}) = {disc}% off')
        if len(seen_urls) >= 10:
            break

conn.close()