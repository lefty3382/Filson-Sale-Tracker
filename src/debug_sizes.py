#!/usr/bin/env python3
"""Debug size information in database."""

import sqlite3

conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if sizes were extracted for any recent items
cursor.execute('''
    SELECT title, sizes, url
    FROM sale_items 
    WHERE scraped_at >= datetime('now', '-10 minutes')
    AND sizes IS NOT NULL
    AND sizes != ''
    ORDER BY title
    LIMIT 10
''')

items = cursor.fetchall()
print(f'Found {len(items)} items with size information:')
for item in items:
    title = item['title']
    sizes = item['sizes'] 
    url = item['url'][:50] + '...' if item['url'] else 'No URL'
    print(f'  {title}')
    print(f'    Sizes: "{sizes}"')
    print(f'    URL: {url}')
    print()

# Also check total items from recent scrape
cursor.execute('SELECT COUNT(*) FROM sale_items WHERE scraped_at >= datetime("now", "-10 minutes")')
total_recent = cursor.fetchone()[0]
print(f'Total recent items: {total_recent}')

# Check how many have empty/null sizes
cursor.execute('''
    SELECT COUNT(*) FROM sale_items 
    WHERE scraped_at >= datetime("now", "-10 minutes")
    AND (sizes IS NULL OR sizes = '' OR sizes = 'N/A')
''')
no_sizes = cursor.fetchone()[0]
print(f'Items without size info: {no_sizes}')

conn.close()