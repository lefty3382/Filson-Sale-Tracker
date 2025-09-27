#!/usr/bin/env python3
"""Check scraping history."""

import sqlite3

conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check when items were last scraped
cursor.execute('SELECT MAX(scraped_at) as latest_scrape FROM sale_items')
latest = cursor.fetchone()['latest_scrape']

cursor.execute('SELECT COUNT(*) as count FROM sale_items WHERE scraped_at = ?', (latest,))
latest_count = cursor.fetchone()['count']

print(f'Latest scrape: {latest}')
print(f'Items from latest scrape: {latest_count}')
print()

# Check all unique scrape dates
cursor.execute('SELECT scraped_at, COUNT(*) as count FROM sale_items GROUP BY scraped_at ORDER BY scraped_at DESC LIMIT 5')
scrapes = cursor.fetchall()
print('Recent scraping sessions:')
for scrape in scrapes:
    scrape_time = scrape['scraped_at']
    count = scrape['count']
    print(f'  {scrape_time}: {count} items')

conn.close()