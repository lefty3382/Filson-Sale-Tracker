#!/usr/bin/env python3
"""Debug the exact database query."""

import sqlite3

conn = sqlite3.connect('sale_tracker.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Run the exact same query as get_discounted_items()
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
print(f'get_discounted_items query returned: {len(items)} items')

if len(items) > 7:
    print()
    print('First 10 items from query:')
    for i, item in enumerate(items[:10]):
        title = item['title']
        price = item['price']
        orig_price = item['original_price']
        discount_pct = item['discount_percent']
        print(f'{i+1}. {title} - ${price} (was ${orig_price}) = {discount_pct}% off')

    # Test deduplication logic
    print()
    print('Testing URL deduplication:')
    urls = [item['url'] for item in items if item['url']]
    unique_urls = set(urls)
    print(f'Total URLs: {len(urls)}')
    print(f'Unique URLs: {len(unique_urls)}')
    
    # Show first few unique URLs
    seen_urls = set()
    deduplicated = []
    for item in items:
        url = item.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduplicated.append(item)
        elif not url:  # Keep items without URLs
            deduplicated.append(item)
    
    print(f'After deduplication: {len(deduplicated)} items')
    
    if len(deduplicated) > 7:
        print()
        print('First 15 deduplicated items:')
        for i, item in enumerate(deduplicated[:15]):
            title = item['title']
            price = item['price']
            orig_price = item['original_price']
            discount_pct = item['discount_percent']
            url = item['url'][:50] + '...' if item['url'] else 'No URL'
            print(f'{i+1}. {title} - ${price} (was ${orig_price}) = {discount_pct}% off')
            print(f'    URL: {url}')

conn.close()