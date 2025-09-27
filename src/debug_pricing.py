#!/usr/bin/env python3
"""Debug pricing data in database."""

import sqlite3

conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check total items vs items with prices
cursor.execute('SELECT COUNT(*) as count FROM sale_items')
total = cursor.fetchone()['count']

cursor.execute('SELECT COUNT(*) as count FROM sale_items WHERE price IS NOT NULL AND price != ""')
with_price = cursor.fetchone()['count']

cursor.execute('SELECT COUNT(*) as count FROM sale_items WHERE original_price IS NOT NULL AND original_price != ""')
with_orig_price = cursor.fetchone()['count']

cursor.execute('SELECT COUNT(*) as count FROM sale_items WHERE discount IS NOT NULL AND discount != ""')
with_discount = cursor.fetchone()['count']

print(f'Total items in DB: {total}')
print(f'Items with price: {with_price}')  
print(f'Items with original_price: {with_orig_price}')
print(f'Items with discount field: {with_discount}')
print()

# Check what the discount query criteria actually returns
cursor.execute('''
    SELECT COUNT(*) as count 
    FROM sale_items 
    WHERE (original_price > price AND price IS NOT NULL AND original_price IS NOT NULL)
       OR (discount IS NOT NULL AND discount != '')
''')
discounted_count = cursor.fetchone()['count']
print(f'Items matching current discount query: {discounted_count}')
print()

# Look at some items without prices
cursor.execute('''
    SELECT title, url, price, original_price, discount, scraped_at
    FROM sale_items 
    WHERE (price IS NULL OR price = "") 
    AND title LIKE "%Tin Cloth%"
    LIMIT 5
''')

print('Tin Cloth items without prices:')
items = cursor.fetchall()
for item in items:
    title = item['title']
    url = item['url'] if item['url'] else 'None'
    price = str(item['price']) if item['price'] else 'NULL'
    orig = str(item['original_price']) if item['original_price'] else 'NULL'
    discount = str(item['discount']) if item['discount'] else 'NULL'
    scraped = item['scraped_at']
    print(f'  {title}')
    print(f'    Price: {price}, Original: {orig}, Discount: {discount}')
    print(f'    URL: {url[:80]}')
    print(f'    Scraped: {scraped}')
    print()

# Look for items that have discount text but no numeric prices
cursor.execute('''
    SELECT title, url, price, original_price, discount, scraped_at
    FROM sale_items 
    WHERE discount IS NOT NULL AND discount != ""
    AND discount NOT LIKE "%off"
    LIMIT 5
''')

print('Items with discount field (not % off):')
discount_items = cursor.fetchall()
for item in discount_items:
    title = item['title']
    url = item['url'] if item['url'] else 'None'  
    price = str(item['price']) if item['price'] else 'NULL'
    orig = str(item['original_price']) if item['original_price'] else 'NULL'
    discount = str(item['discount']) if item['discount'] else 'NULL'
    print(f'  {title}')
    print(f'    Price: {price}, Original: {orig}, Discount: "{discount}"')
    print(f'    URL: {url[:80]}')
    print()

conn.close()