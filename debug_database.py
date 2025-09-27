#!/usr/bin/env python3
"""
Debug script to check database contents
"""

import sys
sys.path.append('src')

from database import Database

# Initialize database
db = Database({'filename': 'sale_tracker.db'})
db.initialize()

# Get all items
all_items = db.get_items()
print(f"Total items in database: {len(all_items)}")

# Get discounted items
discounted_items = db.get_discounted_items()
print(f"Items with detected discounts: {len(discounted_items)}")

# Check unique URLs
unique_urls = set(item['url'] for item in all_items)
print(f"Unique URLs: {len(unique_urls)}")

# Show some sample URLs to see the variety
print(f"\nFirst 10 unique URLs:")
for i, url in enumerate(list(unique_urls)[:10]):
    print(f"{i+1}: {url}")

# Check items from most recent scrape
print(f"\nMost recent scrape (last 20 items):")
for i, item in enumerate(all_items[-20:]):
    print(f"{i+1}: {item['title']} -> {item['url'][:50]}...")