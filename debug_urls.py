#!/usr/bin/env python3
"""
Debug script to check for duplicate URLs
"""

import sys
sys.path.append('src')

from database import Database

# Initialize database
db = Database({'filename': 'sale_tracker.db'})
db.initialize()

# Get all items (not just discounted ones)
items = db.get_items()

print("=== DEBUGGING DUPLICATE ITEMS ===")
print(f"Total discounted items: {len(items)}")

# Check Field Flannel Shirt items
field_flannels = [item for item in items if 'Field Flannel' in item['title']]
print(f"\nField Flannel Shirt items: {len(field_flannels)}")

print("\nFirst 5 Field Flannel Shirt URLs:")
for i, item in enumerate(field_flannels[:5]):
    print(f"{i+1}: {item['title']}")
    print(f"   URL: {item['url']}")
    print()

# Check for unique URLs vs duplicate URLs
all_urls = [item['url'] for item in items]
unique_urls = set(all_urls)
print(f"Total URLs: {len(all_urls)}")
print(f"Unique URLs: {len(unique_urls)}")
print(f"Duplicates: {len(all_urls) - len(unique_urls)}")

# Show some duplicate URLs
from collections import Counter
url_counts = Counter(all_urls)
duplicates = {url: count for url, count in url_counts.items() if count > 1}

if duplicates:
    print(f"\nTop 5 most duplicated URLs:")
    for url, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {count}x: {url}")